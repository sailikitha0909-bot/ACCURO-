from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Entry, User, AuditLog, ExceptionRecord
from app.schemas import EntryOut, EntryUpdate
from app.api.deps import get_current_user, require_role
from app.services.categorisation_engine import CategorisationEngine

router = APIRouter(prefix="/entries", tags=["Accounting Entries"])

@router.get("", response_model=List[EntryOut])
def list_entries(
    client_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Entry).filter(Entry.organization_id == current_user.organization_id)
    if client_id:
        query = query.filter(Entry.client_id == client_id)
    if status_filter:
        query = query.filter(Entry.status == status_filter)

    return query.order_by(Entry.invoice_date.desc()).all()

@router.get("/{entry_id}", response_model=EntryOut)
def get_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entry = db.query(Entry).filter(
        Entry.id == entry_id,
        Entry.organization_id == current_user.organization_id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry

@router.put("/{entry_id}", response_model=EntryOut)
def update_entry(
    entry_id: str,
    entry_update: EntryUpdate,
    current_user: User = Depends(require_role(["partner", "article"])),
    db: Session = Depends(get_db)
):
    entry = db.query(Entry).filter(
        Entry.id == entry_id,
        Entry.organization_id == current_user.organization_id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    old_state = {
        "invoice_number": entry.invoice_number,
        "taxable_value_paise": entry.taxable_value_paise,
        "total_amount_paise": entry.total_amount_paise,
        "debit_account_id": entry.debit_account_id,
        "status": entry.status
    }

    update_dict = entry_update.dict(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(entry, field, val)

    # If CA corrected debit ledger account, teach rule engine
    if entry_update.debit_account_id and entry_update.debit_account_id != old_state["debit_account_id"]:
        CategorisationEngine.learn_ca_correction(
            db=db,
            organization_id=current_user.organization_id,
            client_id=entry.client_id,
            party_name=entry.party_name,
            target_account_id=entry_update.debit_account_id
        )

    db.commit()
    db.refresh(entry)

    # Audit Trail
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="entry_edited",
        entity_type="entry",
        entity_id=entry.id,
        details={"before": old_state, "after": update_dict}
    )
    db.add(audit)
    db.commit()

    return entry

@router.post("/{entry_id}/approve", response_model=EntryOut)
def approve_entry(
    entry_id: str,
    current_user: User = Depends(require_role(["partner"])), # Strictly Partner/CA only!
    db: Session = Depends(get_db)
):
    entry = db.query(Entry).filter(
        Entry.id == entry_id,
        Entry.organization_id == current_user.organization_id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    entry.status = "final"
    entry.approved_by_user_id = current_user.id
    entry.approved_at = datetime.now(timezone.utc)

    # Auto-resolve any open exceptions on this entry upon CA approval
    exceptions = db.query(ExceptionRecord).filter(
        ExceptionRecord.entry_id == entry.id,
        ExceptionRecord.status == "open"
    ).all()
    for exc in exceptions:
        exc.status = "resolved"
        exc.resolved_by_user_id = current_user.id
        exc.resolved_at = datetime.now(timezone.utc)
        exc.resolution_note = "Approved by CA Partner"

    db.commit()
    db.refresh(entry)

    # Audit log
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="entry_approved_by_ca",
        entity_type="entry",
        entity_id=entry.id,
        details={
            "invoice_number": entry.invoice_number,
            "party_name": entry.party_name,
            "total_amount_paise": entry.total_amount_paise,
            "status": "final"
        }
    )
    db.add(audit)
    db.commit()

    return entry

@router.post("/{entry_id}/reject", response_model=EntryOut)
def reject_entry(
    entry_id: str,
    reason: str = "Rejected during CA review",
    current_user: User = Depends(require_role(["partner"])),
    db: Session = Depends(get_db)
):
    entry = db.query(Entry).filter(
        Entry.id == entry_id,
        Entry.organization_id == current_user.organization_id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    entry.status = "rejected"
    db.commit()

    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="entry_rejected_by_ca",
        entity_type="entry",
        entity_id=entry.id,
        details={"reason": reason}
    )
    db.add(audit)
    db.commit()

    return entry
