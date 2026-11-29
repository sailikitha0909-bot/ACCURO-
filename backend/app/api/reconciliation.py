import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models import GSTR2BRecord, BankStatement, BankStatementLine, Client, User, AuditLog
from app.api.deps import get_current_user, require_role
from app.services.gstr2b_parser import GSTR2BParser
from app.services.bank_parser import BankParser
from app.services.reconciliation_engine import ReconciliationEngine

router = APIRouter(prefix="/reconciliation", tags=["Reconciliation"])

@router.post("/gstr2b/upload")
async def upload_gstr2b(
    client_id: str = Form(...),
    return_period: str = Form(...), # e.g. "072024" or "2024-07"
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(["partner", "article"])),
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.organization_id == current_user.organization_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    content = await file.read()
    filename_lower = file.filename.lower()

    if filename_lower.endswith(".json"):
        records_data = GSTR2BParser.parse_json(content)
    elif filename_lower.endswith(".xlsx"):
        # Save temp file for openpyxl
        temp_path = os.path.join(settings.STORAGE_LOCAL_DIR, f"temp_{file.filename}")
        with open(temp_path, "wb") as f:
            f.write(content)
        records_data = GSTR2BParser.parse_excel(temp_path)
        try:
            os.remove(temp_path)
        except Exception:
            pass
    else:
        raise HTTPException(status_code=400, detail="Only .json or .xlsx GSTR-2B files are supported.")

    # Save to database
    saved_records = []
    for r in records_data:
        rec = GSTR2BRecord(
            organization_id=current_user.organization_id,
            client_id=client.id,
            return_period=return_period,
            supplier_gstin=r["supplier_gstin"],
            supplier_name=r["supplier_name"],
            invoice_number=r["invoice_number"],
            invoice_date=r["invoice_date"],
            taxable_value_paise=r["taxable_value_paise"],
            igst_paise=r["igst_paise"],
            cgst_paise=r["cgst_paise"],
            sgst_paise=r["sgst_paise"],
            cess_paise=r["cess_paise"],
            itc_availability=r.get("itc_availability", "Y"),
            itc_reason=r.get("itc_reason"),
            reconciliation_status="gstr2b_only"
        )
        db.add(rec)
        saved_records.append(rec)

    db.commit()

    # Automatically trigger reconciliation pass
    rec_result = ReconciliationEngine.match_books_with_gstr2b(
        db=db,
        client_id=client.id,
        return_period=return_period
    )

    return {
        "status": "success",
        "imported_count": len(saved_records),
        "reconciliation_summary": rec_result
    }

@router.get("/gstr2b/summary")
def get_gstr2b_summary(
    client_id: str,
    return_period: str = "072024",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = ReconciliationEngine.match_books_with_gstr2b(
        db=db,
        client_id=client_id,
        return_period=return_period
    )
    return result

@router.post("/bank/upload")
async def upload_bank_statement(
    client_id: str = Form(...),
    bank_name: str = Form("HDFC Bank"),
    account_number: str = Form("XXXXXX9921"),
    statement_period: str = Form("July 2024"),
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(["partner", "article"])),
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.organization_id == current_user.organization_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    content = await file.read()
    filename_lower = file.filename.lower()

    if filename_lower.endswith(".csv"):
        parsed_lines = BankParser.parse_csv(content)
    elif filename_lower.endswith(".xlsx"):
        # Temporary fallback for xlsx
        temp_path = os.path.join(settings.STORAGE_LOCAL_DIR, f"temp_bank_{file.filename}")
        with open(temp_path, "wb") as f:
            f.write(content)
        parsed_lines = BankParser.parse_csv(content)
        try: os.remove(temp_path)
        except Exception: pass
    else:
        raise HTTPException(status_code=400, detail="Only CSV or Excel bank statement files are supported.")

    stmt = BankStatement(
        organization_id=current_user.organization_id,
        client_id=client.id,
        bank_name=bank_name,
        account_number_masked=account_number,
        statement_period=statement_period
    )
    db.add(stmt)
    db.flush()

    for l in parsed_lines:
        line = BankStatementLine(
            statement_id=stmt.id,
            txn_date=l["txn_date"],
            narration=l["narration"],
            reference_no=l["reference_no"],
            debit_paise=l["debit_paise"],
            credit_paise=l["credit_paise"],
            balance_paise=l["balance_paise"],
            reconciliation_status="unmatched"
        )
        db.add(line)

    db.commit()

    # Run bank matching pass
    match_result = ReconciliationEngine.match_bank_statement(
        db=db,
        statement_id=stmt.id,
        client_id=client.id
    )

    return {
        "status": "success",
        "statement_id": stmt.id,
        "total_lines": len(parsed_lines),
        "reconciliation": match_result
    }

@router.get("/bank/statements")
def list_bank_statements(
    client_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    stmts = db.query(BankStatement).filter(BankStatement.client_id == client_id).all()
    results = []
    for s in stmts:
        matched = sum(1 for l in s.lines if l.reconciliation_status == "matched")
        unmatched = len(s.lines) - matched
        results.append({
            "id": s.id,
            "bank_name": s.bank_name,
            "account_number": s.account_number_masked,
            "statement_period": s.statement_period,
            "total_lines": len(s.lines),
            "matched_count": matched,
            "unmatched_count": unmatched,
            "uploaded_at": s.uploaded_at.isoformat()
        })
    return results

@router.get("/bank/statements/{statement_id}/lines")
def get_bank_statement_lines(
    statement_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    lines = db.query(BankStatementLine).filter(BankStatementLine.statement_id == statement_id).all()
    return lines
