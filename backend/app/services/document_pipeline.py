import os
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import (
    Document, Entry, ExceptionRecord, Client, FinancialYear, AuditLog
)
from app.services.extraction_provider import get_extraction_provider
from app.services.validation_engine import ValidationEngine
from app.services.categorisation_engine import CategorisationEngine

def compute_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

class DocumentPipeline:
    @staticmethod
    def process_document(db: Session, document_id: str) -> Document:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        doc.status = "processing"
        db.commit()

        try:
            client = db.query(Client).filter(Client.id == doc.client_id).first()
            if not client:
                raise ValueError("Associated client not found")

            # Get active financial year
            fy = None
            if doc.financial_year_id:
                fy = db.query(FinancialYear).filter(FinancialYear.id == doc.financial_year_id).first()
            if not fy:
                fy = db.query(FinancialYear).filter(
                    FinancialYear.client_id == doc.client_id,
                    FinancialYear.is_locked == False
                ).order_by(FinancialYear.start_date.desc()).first()

            fy_start = fy.start_date if fy else datetime(2024, 4, 1, tzinfo=timezone.utc)
            fy_end = fy.end_date if fy else datetime(2025, 3, 31, tzinfo=timezone.utc)

            # Step 1 & 2: Extract Data via Extraction Provider
            provider = get_extraction_provider()
            raw_extraction = provider.extract_document(doc.storage_path, doc.filename, doc.file_type)
            doc.extraction_data = raw_extraction

            # Step 3: Parse extracted fields into Entry schema
            inv_date_str = raw_extraction.get("invoice_date", {}).get("value")
            inv_date = None
            if inv_date_str:
                try:
                    inv_date = datetime.fromisoformat(inv_date_str.replace("Z", "+00:00"))
                except Exception:
                    inv_date = datetime.now(timezone.utc)
            else:
                inv_date = datetime.now(timezone.utc)

            taxable_p = raw_extraction.get("taxable_value_paise", {}).get("value", 0)
            cgst_p = raw_extraction.get("cgst_paise", {}).get("value", 0)
            sgst_p = raw_extraction.get("sgst_paise", {}).get("value", 0)
            igst_p = raw_extraction.get("igst_paise", {}).get("value", 0)
            cess_p = raw_extraction.get("cess_paise", {}).get("value", 0)
            round_off_p = raw_extraction.get("round_off_paise", {}).get("value", 0)
            total_p = raw_extraction.get("total_amount_paise", {}).get("value", 0)
            party_name = raw_extraction.get("supplier_name", {}).get("value", "Unknown Supplier")
            party_gstin = raw_extraction.get("supplier_gstin", {}).get("value", "")
            pos = raw_extraction.get("place_of_supply", {}).get("value", client.state_code)
            line_items = raw_extraction.get("line_items", [])

            # Step 4: Categorisation Engine
            hsn_code = line_items[0].get("hsn_sac") if line_items else None
            account_id, cat_conf, cat_source = CategorisationEngine.resolve_category(
                db=db,
                client_id=client.id,
                party_name=party_name,
                line_items=line_items,
                hsn_code=hsn_code
            )

            # Check if entry already exists for this document
            existing_entry = db.query(Entry).filter(Entry.document_id == doc.id).first()
            if not existing_entry:
                entry = Entry(
                    organization_id=doc.organization_id,
                    client_id=doc.client_id,
                    financial_year_id=fy.id if fy else None,
                    document_id=doc.id,
                    entry_type="purchase",
                    invoice_number=raw_extraction.get("invoice_number", {}).get("value", "INV-UNKNOWN"),
                    invoice_date=inv_date,
                    party_name=party_name,
                    party_gstin=party_gstin,
                    place_of_supply=pos,
                    taxable_value_paise=taxable_p,
                    cgst_paise=cgst_p,
                    sgst_paise=sgst_p,
                    igst_paise=igst_p,
                    cess_paise=cess_p,
                    round_off_paise=round_off_p,
                    total_amount_paise=total_p,
                    line_items=line_items,
                    debit_account_id=account_id,
                    status="draft", # AI drafted, requires CA approval
                    is_itc_eligible=True
                )
                db.add(entry)
                db.flush()
            else:
                entry = existing_entry
                entry.invoice_number = raw_extraction.get("invoice_number", {}).get("value", entry.invoice_number)
                entry.invoice_date = inv_date
                entry.party_name = party_name
                entry.party_gstin = party_gstin
                entry.place_of_supply = pos
                entry.taxable_value_paise = taxable_p
                entry.cgst_paise = cgst_p
                entry.sgst_paise = sgst_p
                entry.igst_paise = igst_p
                entry.cess_paise = cess_p
                entry.total_amount_paise = total_p
                entry.line_items = line_items
                if account_id:
                    entry.debit_account_id = account_id

            # Step 5: Deterministic Validation Engine
            past_entries = [
                {"id": e.id, "invoice_number": e.invoice_number, "party_gstin": e.party_gstin, "total_amount_paise": e.total_amount_paise, "invoice_date": e.invoice_date.isoformat()}
                for e in db.query(Entry).filter(Entry.client_id == client.id, Entry.id != entry.id).all()
            ]

            vendor_history = [
                {"total_amount_paise": e.total_amount_paise}
                for e in db.query(Entry).filter(Entry.client_id == client.id, Entry.party_name == party_name, Entry.id != entry.id).all()
            ]

            entry_dict = {
                "id": entry.id,
                "invoice_number": entry.invoice_number,
                "invoice_date": entry.invoice_date,
                "party_name": entry.party_name,
                "party_gstin": entry.party_gstin,
                "place_of_supply": entry.place_of_supply,
                "taxable_value_paise": entry.taxable_value_paise,
                "cgst_paise": entry.cgst_paise,
                "sgst_paise": entry.sgst_paise,
                "igst_paise": entry.igst_paise,
                "cess_paise": entry.cess_paise,
                "round_off_paise": entry.round_off_paise,
                "total_amount_paise": entry.total_amount_paise,
                "line_items": entry.line_items,
            }

            validation_issues = ValidationEngine.validate_entry(
                entry_data=entry_dict,
                client_state_code=client.state_code,
                fy_start_date=fy_start,
                fy_end_date=fy_end,
                existing_entries=past_entries,
                vendor_history=vendor_history
            )

            # Clear old exceptions for this document if re-processing
            db.query(ExceptionRecord).filter(ExceptionRecord.document_id == doc.id).delete()

            has_high_severity = False
            for issue in validation_issues:
                if issue.severity == "high":
                    has_high_severity = True

                # If blocked credit detected, mark entry ITC ineligibility note
                if issue.exception_type == "blocked_credit_17_5":
                    entry.is_itc_eligible = False
                    entry.itc_blocked_reason = issue.description

                exc_rec = ExceptionRecord(
                    organization_id=doc.organization_id,
                    client_id=doc.client_id,
                    document_id=doc.id,
                    entry_id=entry.id,
                    severity=issue.severity,
                    exception_type=issue.exception_type,
                    title=issue.title,
                    description=issue.description,
                    evidence=issue.evidence,
                    suggested_fix=issue.suggested_fix,
                    status="open"
                )
                db.add(exc_rec)

            doc.processed_at = datetime.now(timezone.utc)
            if validation_issues:
                doc.status = "needs_attention"
            else:
                doc.status = "done"

            # Create immutable audit log
            audit = AuditLog(
                organization_id=doc.organization_id,
                user_id=doc.uploaded_by_user_id,
                action="ai_extraction_completed",
                entity_type="document",
                entity_id=doc.id,
                details={
                    "filename": doc.filename,
                    "issues_count": len(validation_issues),
                    "has_high_severity": has_high_severity,
                    "entry_id": entry.id,
                    "total_amount_paise": total_p
                }
            )
            db.add(audit)
            db.commit()

            return doc

        except Exception as e:
            db.rollback()
            doc.status = "failed"
            doc.error_message = str(e)
            db.commit()
            raise e
