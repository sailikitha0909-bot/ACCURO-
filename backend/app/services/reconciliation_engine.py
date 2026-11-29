import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models import Entry, GSTR2BRecord, BankStatementLine, ExceptionRecord

def normalize_invoice_number(inv_num: str) -> str:
    """Normalize invoice number by stripping punctuation, spaces, and leading zeros from numeric components."""
    if not inv_num:
        return ""
    # Strip leading zeros within segments: e.g. /0014 -> /14, -001 -> -1
    s = re.sub(r'(^|[^0-9])0+([0-9]+)', r'\1\2', inv_num.strip())
    # Strip non-alphanumeric
    cleaned = re.sub(r'[^A-Za-z0-9]', '', s).upper()
    return cleaned

class ReconciliationEngine:
    @staticmethod
    def match_books_with_gstr2b(
        db: Session,
        client_id: str,
        return_period: str,
        date_tolerance_days: int = 15,
        amount_tolerance_paise: int = 500 # ₹5.00
    ) -> Dict[str, Any]:
        """
        Deterministic multi-pass reconciliation of accounting books vs GSTR-2B.
        """
        # Fetch purchase entries in books for this client
        entries = db.query(Entry).filter(
            Entry.client_id == client_id,
            Entry.entry_type == "purchase"
        ).all()

        # Fetch GSTR-2B records for this return period
        records = db.query(GSTR2BRecord).filter(
            GSTR2BRecord.client_id == client_id,
            GSTR2BRecord.return_period == return_period
        ).all()

        matched_entry_ids = set()
        matched_record_ids = set()

        matched_results = []
        partial_results = []
        books_only_results = []
        gstr2b_only_results = []

        # Pass 1: Exact Match (GSTIN + Normalized Invoice Number)
        for rec in records:
            norm_rec_inv = normalize_invoice_number(rec.invoice_number)
            rec_gstin = (rec.supplier_gstin or "").upper().strip()

            for entry in entries:
                if entry.id in matched_entry_ids:
                    continue
                
                entry_gstin = (entry.party_gstin or "").upper().strip()
                norm_entry_inv = normalize_invoice_number(entry.invoice_number)

                if rec_gstin == entry_gstin and norm_rec_inv == norm_entry_inv:
                    # Found candidate by invoice number & GSTIN
                    books_tax = entry.cgst_paise + entry.sgst_paise + entry.igst_paise + entry.cess_paise
                    gstr2b_tax = rec.cgst_paise + rec.sgst_paise + rec.igst_paise + rec.cess_paise

                    tax_diff_paise = abs(books_tax - gstr2b_tax)
                    val_diff_paise = abs(entry.taxable_value_paise - rec.taxable_value_paise)

                    discrepancies = {}
                    if tax_diff_paise > amount_tolerance_paise:
                        discrepancies["tax_mismatch"] = {
                            "books_tax_paise": books_tax,
                            "gstr2b_tax_paise": gstr2b_tax,
                            "diff_paise": tax_diff_paise
                        }
                    if val_diff_paise > amount_tolerance_paise:
                        discrepancies["taxable_value_mismatch"] = {
                            "books_taxable_paise": entry.taxable_value_paise,
                            "gstr2b_taxable_paise": rec.taxable_value_paise,
                            "diff_paise": val_diff_paise
                        }

                    if discrepancies:
                        rec.reconciliation_status = "partially_matched"
                        rec.matched_entry_id = entry.id
                        rec.match_score = 0.85
                        rec.match_discrepancies = discrepancies
                        partial_results.append({
                            "gstr2b_record": rec,
                            "book_entry": entry,
                            "reason": "Exact invoice match with value/tax discrepancies",
                            "discrepancies": discrepancies
                        })
                    else:
                        rec.reconciliation_status = "matched"
                        rec.matched_entry_id = entry.id
                        rec.match_score = 1.0
                        rec.match_discrepancies = {}
                        matched_results.append({
                            "gstr2b_record": rec,
                            "book_entry": entry,
                            "reason": "Exact match on GSTIN and invoice number"
                        })

                    matched_entry_ids.add(entry.id)
                    matched_record_ids.add(rec.id)
                    break

        # Pass 2: Tolerant & Fuzzy Match (Same GSTIN + same total tax within tolerance + date window)
        unmatched_records = [r for r in records if r.id not in matched_record_ids]
        for rec in unmatched_records:
            rec_gstin = (rec.supplier_gstin or "").upper().strip()
            gstr2b_tax = rec.cgst_paise + rec.sgst_paise + rec.igst_paise + rec.cess_paise

            for entry in entries:
                if entry.id in matched_entry_ids:
                    continue

                entry_gstin = (entry.party_gstin or "").upper().strip()
                if rec_gstin == entry_gstin:
                    books_tax = entry.cgst_paise + entry.sgst_paise + entry.igst_paise + entry.cess_paise
                    tax_diff = abs(books_tax - gstr2b_tax)
                    
                    # Date window
                    days_diff = abs((rec.invoice_date - entry.invoice_date).days) if rec.invoice_date and entry.invoice_date else 999

                    if tax_diff <= amount_tolerance_paise and days_diff <= date_tolerance_days:
                        rec.reconciliation_status = "matched"
                        rec.matched_entry_id = entry.id
                        rec.match_score = 0.90
                        rec.match_discrepancies = {
                            "tolerant_match": f"Invoice numbers slightly differ ('{entry.invoice_number}' vs '{rec.invoice_number}'), matched via GSTIN, date, and tax amount."
                        }
                        matched_results.append({
                            "gstr2b_record": rec,
                            "book_entry": entry,
                            "reason": f"Tolerant match (date delta {days_diff} days, amount match)"
                        })
                        matched_entry_ids.add(entry.id)
                        matched_record_ids.add(rec.id)
                        break

        # Pass 3: In GSTR-2B Not in Books
        for rec in records:
            if rec.id not in matched_record_ids:
                rec.reconciliation_status = "gstr2b_only"
                rec.matched_entry_id = None
                rec.match_score = 0.0
                gstr2b_only_results.append({
                    "gstr2b_record": rec,
                    "reason": "Invoice uploaded by supplier in GSTR-1 but not found in accounting books"
                })

        # Pass 4: In Books Not in GSTR-2B
        for entry in entries:
            if entry.id not in matched_entry_ids:
                books_only_results.append({
                    "book_entry": entry,
                    "reason": "Recorded in books but missing in GSTR-2B (Supplier hasn't filed GSTR-1)"
                })

        db.commit()

        # Compute ITC summary metrics
        total_eligible_itc_paise = 0
        total_at_risk_itc_paise = 0
        total_blocked_itc_paise = 0
        vendor_followups = {}

        for item in matched_results:
            rec = item["gstr2b_record"]
            entry = item["book_entry"]
            tax = entry.cgst_paise + entry.sgst_paise + entry.igst_paise + entry.cess_paise
            if not entry.is_itc_eligible:
                total_blocked_itc_paise += tax
            elif rec.itc_availability == "N":
                total_blocked_itc_paise += tax
            else:
                total_eligible_itc_paise += tax

        for item in partial_results:
            entry = item["book_entry"]
            tax = entry.cgst_paise + entry.sgst_paise + entry.igst_paise + entry.cess_paise
            total_at_risk_itc_paise += tax

        for item in books_only_results:
            entry = item["book_entry"]
            tax = entry.cgst_paise + entry.sgst_paise + entry.igst_paise + entry.cess_paise
            total_at_risk_itc_paise += tax

            # Group for vendor follow-up
            v_key = entry.party_gstin or entry.party_name
            if v_key not in vendor_followups:
                vendor_followups[v_key] = {
                    "supplier_name": entry.party_name,
                    "supplier_gstin": entry.party_gstin,
                    "missing_invoices_count": 0,
                    "itc_at_risk_paise": 0,
                    "invoices": []
                }
            vendor_followups[v_key]["missing_invoices_count"] += 1
            vendor_followups[v_key]["itc_at_risk_paise"] += tax
            vendor_followups[v_key]["invoices"].append({
                "invoice_number": entry.invoice_number,
                "invoice_date": entry.invoice_date.strftime("%d-%b-%Y") if entry.invoice_date else "",
                "tax_paise": tax
            })

        return {
            "matched_count": len(matched_results),
            "partial_count": len(partial_results),
            "books_only_count": len(books_only_results),
            "gstr2b_only_count": len(gstr2b_only_results),
            "itc_summary": {
                "eligible_itc_paise": total_eligible_itc_paise,
                "at_risk_itc_paise": total_at_risk_itc_paise,
                "blocked_itc_paise": total_blocked_itc_paise,
                "total_books_itc_paise": total_eligible_itc_paise + total_at_risk_itc_paise + total_blocked_itc_paise,
            },
            "vendor_followups": list(vendor_followups.values())
        }

    @staticmethod
    def match_bank_statement(
        db: Session,
        statement_id: str,
        client_id: str,
        date_window_days: int = 5
    ) -> Dict[str, Any]:
        """
        Reconcile bank statement transactions with ledger entries (Payment & Receipt vouchers).
        """
        lines = db.query(BankStatementLine).filter(
            BankStatementLine.statement_id == statement_id
        ).all()

        entries = db.query(Entry).filter(
            Entry.client_id == client_id
        ).all()

        matched_line_ids = set()
        matched_entry_ids = set()

        matched_pairs = []

        for line in lines:
            line_amount = line.debit_paise if line.debit_paise > 0 else line.credit_paise
            if line_amount == 0:
                continue

            ref_no = (line.reference_no or "").strip().upper()
            narration = (line.narration or "").upper()

            for entry in entries:
                if entry.id in matched_entry_ids:
                    continue

                entry_amount = entry.total_amount_paise
                amount_matched = (abs(entry_amount - line_amount) <= 100) # within ₹1

                # UTR / Reference match
                ref_matched = False
                if ref_no and len(ref_no) > 4:
                    if ref_no in narration or ref_no in (entry.voucher_number or "").upper():
                        ref_matched = True

                # Party name keyword match in narration
                party_in_narration = False
                if entry.party_name:
                    p_words = [w.strip() for w in entry.party_name.upper().split() if len(w.strip()) > 3]
                    if any(w in narration for w in p_words):
                        party_in_narration = True

                # Date tolerance
                days_diff = abs((line.txn_date - entry.invoice_date).days) if line.txn_date and entry.invoice_date else 999

                if (amount_matched and (ref_matched or party_in_narration or days_diff <= date_window_days)):
                    line.reconciliation_status = "matched"
                    line.matched_entry_id = entry.id
                    line.match_reason = f"Matched on amount (₹{line_amount/100:.2f}) and {'UTR reference' if ref_matched else 'narration/date window'}"
                    matched_line_ids.add(line.id)
                    matched_entry_ids.add(entry.id)
                    matched_pairs.append({
                        "bank_line_id": line.id,
                        "entry_id": entry.id,
                        "amount_paise": line_amount,
                        "reason": line.match_reason
                    })
                    break

        db.commit()

        unmatched_lines = [l for l in lines if l.id not in matched_line_ids]

        return {
            "total_lines": len(lines),
            "matched_lines_count": len(matched_pairs),
            "unmatched_lines_count": len(unmatched_lines),
            "matched_pairs": matched_pairs
        }
