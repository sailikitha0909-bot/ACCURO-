from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models import Entry, Client, User, ChartOfAccount, GSTR2BRecord, AuditLog
from app.api.deps import get_current_user, require_role
from app.services.export_service import ExportService
from app.services.reconciliation_engine import ReconciliationEngine

router = APIRouter(prefix="/reports", tags=["Reports & Exports"])

@router.get("/trial-balance")
def get_trial_balance(
    client_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    accounts = db.query(ChartOfAccount).filter(ChartOfAccount.client_id == client_id).all()
    entries = db.query(Entry).filter(Entry.client_id == client_id, Entry.status == "final").all()

    # Aggregate debits and credits by ledger
    balances = {}
    for acc in accounts:
        balances[acc.id] = {
            "account_code": acc.account_code,
            "account_name": acc.account_name,
            "account_type": acc.account_type,
            "parent_group": acc.parent_group,
            "debit_paise": 0,
            "credit_paise": 0,
        }

    for e in entries:
        taxable_p = e.taxable_value_paise
        total_p = e.total_amount_paise

        # Debit Expense / Asset
        if e.debit_account_id and e.debit_account_id in balances:
            balances[e.debit_account_id]["debit_paise"] += taxable_p

        # Credit Supplier (Sundry Creditor)
        # Find Sundry Creditor account or first liability
        creditor_acc = next((a for a in accounts if "creditor" in a.account_name.lower()), None)
        if creditor_acc and creditor_acc.id in balances:
            balances[creditor_acc.id]["credit_paise"] += total_p

        # Debit GST Input Tax Credit
        cgst_acc = next((a for a in accounts if "cgst input" in a.account_name.lower()), None)
        sgst_acc = next((a for a in accounts if "sgst input" in a.account_name.lower()), None)
        igst_acc = next((a for a in accounts if "igst input" in a.account_name.lower()), None)

        if e.cgst_paise > 0 and cgst_acc and cgst_acc.id in balances:
            balances[cgst_acc.id]["debit_paise"] += e.cgst_paise
        if e.sgst_paise > 0 and sgst_acc and sgst_acc.id in balances:
            balances[sgst_acc.id]["debit_paise"] += e.sgst_paise
        if e.igst_paise > 0 and igst_acc and igst_acc.id in balances:
            balances[igst_acc.id]["debit_paise"] += e.igst_paise

    tb_rows = [b for b in balances.values() if b["debit_paise"] > 0 or b["credit_paise"] > 0]
    total_debit = sum(r["debit_paise"] for r in tb_rows)
    total_credit = sum(r["credit_paise"] for r in tb_rows)

    return {
        "client_name": client.legal_name,
        "as_of_date": datetime.now().strftime("%d-%b-%Y"),
        "total_debit_paise": total_debit,
        "total_credit_paise": total_credit,
        "is_balanced": (abs(total_debit - total_credit) <= 500), # within rounding paise
        "accounts": tb_rows
    }

@router.get("/gstr-3b-working")
def get_gstr3b_working(
    client_id: str,
    period: str = "July 2024",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entries = db.query(Entry).filter(
        Entry.client_id == client_id,
        Entry.status.in_(["final", "draft"])
    ).all()

    # Table 3.1: Outward Supplies (Sales)
    sales = [e for e in entries if e.entry_type == "sales"]
    outward_txval = sum(e.taxable_value_paise for e in sales)
    outward_igst = sum(e.igst_paise for e in sales)
    outward_cgst = sum(e.cgst_paise for e in sales)
    outward_sgst = sum(e.sgst_paise for e in sales)

    # Table 4: Eligible ITC (Purchases)
    purchases = [e for e in entries if e.entry_type == "purchase"]
    eligible_purchases = [e for e in purchases if e.is_itc_eligible]
    blocked_purchases = [e for e in purchases if not e.is_itc_eligible]

    itc_igst = sum(e.igst_paise for e in eligible_purchases)
    itc_cgst = sum(e.cgst_paise for e in eligible_purchases)
    itc_sgst = sum(e.sgst_paise for e in eligible_purchases)
    itc_cess = sum(e.cess_paise for e in eligible_purchases)

    blocked_tax = sum(e.cgst_paise + e.sgst_paise + e.igst_paise for e in blocked_purchases)

    return {
        "period": period,
        "table_3_1_outward_supplies": {
            "taxable_value_paise": outward_txval,
            "igst_paise": outward_igst,
            "cgst_paise": outward_cgst,
            "sgst_paise": outward_sgst,
        },
        "table_4_itc": {
            "all_other_itc_igst_paise": itc_igst,
            "all_other_itc_cgst_paise": itc_cgst,
            "all_other_itc_sgst_paise": itc_sgst,
            "all_other_itc_cess_paise": itc_cess,
            "ineligible_itc_17_5_paise": blocked_tax,
        },
        "net_gst_payable_paise": {
            "igst_paise": max(0, outward_igst - itc_igst),
            "cgst_paise": max(0, outward_cgst - itc_cgst),
            "sgst_paise": max(0, outward_sgst - itc_sgst),
        }
    }

@router.get("/day-book")
def get_day_book(
    client_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entries = db.query(Entry).filter(
        Entry.client_id == client_id
    ).order_by(Entry.invoice_date.desc()).all()
    return entries

# -----------------
# EXPORT ENDPOINTS
# -----------------
@router.get("/export/tally")
def export_tally_xml(
    client_id: str,
    current_user: User = Depends(require_role(["partner"])), # CA Partner role only
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Export approved final entries
    entries = db.query(Entry).filter(
        Entry.client_id == client_id,
        Entry.status == "final"
    ).all()

    if not entries:
        # Fallback to all entries if no final entries yet
        entries = db.query(Entry).filter(Entry.client_id == client_id).all()

    xml_content = ExportService.generate_tally_xml(entries, company_name=client.legal_name)

    # Log export in audit trail
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="export_tally_xml",
        entity_type="client",
        entity_id=client.id,
        details={"vouchers_count": len(entries), "format": "Tally Prime XML"}
    )
    db.add(audit)
    db.commit()

    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename=Accuro_Tally_Import_{client.legal_name.replace(' ', '_')}.xml"}
    )

@router.get("/export/excel")
def export_excel_report(
    client_id: str,
    report_type: str = "trial_balance",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(Client.id == client_id).first()
    entries = db.query(Entry).filter(Entry.client_id == client_id).all()

    headers = ["Date", "Invoice No", "Party Name", "GSTIN", "Taxable (₹)", "CGST (₹)", "SGST (₹)", "IGST (₹)", "Total (₹)", "Status"]
    rows = []
    for e in entries:
        rows.append([
            e.invoice_date.strftime("%d-%b-%Y") if e.invoice_date else "",
            e.invoice_number,
            e.party_name,
            e.party_gstin or "N/A",
            e.taxable_value_paise / 100.0,
            e.cgst_paise / 100.0,
            e.sgst_paise / 100.0,
            e.igst_paise / 100.0,
            e.total_amount_paise / 100.0,
            e.status.upper()
        ])

    excel_io = ExportService.generate_excel_report(
        report_type=report_type,
        data={"headers": headers, "rows": rows},
        client_name=client.legal_name if client else "Client"
    )

    return StreamingResponse(
        excel_io,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=Accuro_{report_type}_{datetime.now().strftime('%Y%m%d')}.xlsx"}
    )

@router.get("/export/pdf")
def export_pdf_report(
    client_id: str,
    report_type: str = "accounting_vouchers",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(Client.id == client_id).first()
    entries = db.query(Entry).filter(Entry.client_id == client_id).limit(50).all()

    headers = ["Date", "Invoice #", "Party Name", "Taxable (₹)", "Tax (₹)", "Total (₹)", "Status"]
    rows = []
    for e in entries:
        rows.append([
            e.invoice_date.strftime("%d-%b-%Y") if e.invoice_date else "",
            e.invoice_number[:12],
            e.party_name[:22],
            f"₹{e.taxable_value_paise / 100.0:,.2f}",
            f"₹{(e.cgst_paise + e.sgst_paise + e.igst_paise) / 100.0:,.2f}",
            f"₹{e.total_amount_paise / 100.0:,.2f}",
            e.status.upper()
        ])

    pdf_io = ExportService.generate_pdf_report(
        title="Accounting Vouchers Schedule",
        client_name=client.legal_name if client else "Client",
        rows=rows,
        headers=headers
    )

    return StreamingResponse(
        pdf_io,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Accuro_Report_{datetime.now().strftime('%Y%m%d')}.pdf"}
    )
