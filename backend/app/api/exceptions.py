from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import ExceptionRecord, Entry, Document, User, AuditLog
from app.schemas import ExceptionOut, ExceptionAction, BulkExceptionAction
from app.api.deps import get_current_user, require_role

router = APIRouter(prefix="/exceptions", tags=["Exceptions Queue"])

@router.get("", response_model=List[ExceptionOut])
def list_exceptions(
    client_id: Optional[str] = None,
    severity: Optional[str] = None,
    status_filter: Optional[str] = "open",
    exception_type: Optional[str] = None,
    assigned_to: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(ExceptionRecord).filter(
        ExceptionRecord.organization_id == current_user.organization_id
    )

    if client_id:
        query = query.filter(ExceptionRecord.client_id == client_id)
    if severity:
        query = query.filter(ExceptionRecord.severity == severity)
    if status_filter and status_filter != "all":
        query = query.filter(ExceptionRecord.status == status_filter)
    if exception_type:
        query = query.filter(ExceptionRecord.exception_type == exception_type)
    if assigned_to:
        query = query.filter(ExceptionRecord.assigned_to_user_id == assigned_to)

    # Order by severity priority (High first, then Medium, then Low) and creation date
    # In SQLite / PostgreSQL, we can order by CASE or query sorting
    return query.order_by(
        ExceptionRecord.severity == "high",
        ExceptionRecord.severity == "medium",
        ExceptionRecord.created_at.desc()
    ).all()

@router.get("/{exception_id}", response_model=ExceptionOut)
def get_exception(
    exception_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    exc = db.query(ExceptionRecord).filter(
        ExceptionRecord.id == exception_id,
        ExceptionRecord.organization_id == current_user.organization_id
    ).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Exception record not found")
    return exc

@router.post("/{exception_id}/action", response_model=ExceptionOut)
def act_on_exception(
    exception_id: str,
    action_in: ExceptionAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    exc = db.query(ExceptionRecord).filter(
        ExceptionRecord.id == exception_id,
        ExceptionRecord.organization_id == current_user.organization_id
    ).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Exception record not found")

    action = action_in.action.lower()

    if action == "assign":
        exc.assigned_to_user_id = action_in.assigned_to_user_id
    elif action == "resolve":
        exc.status = "resolved"
        exc.resolved_by_user_id = current_user.id
        exc.resolved_at = datetime.now(timezone.utc)
        exc.resolution_note = action_in.resolution_note or "Resolved manually"
    elif action == "reject":
        exc.status = "rejected"
        exc.resolved_by_user_id = current_user.id
        exc.resolved_at = datetime.now(timezone.utc)
        exc.resolution_note = action_in.resolution_note or "Exception rejected"
    elif action == "approve":
        # Requires Partner/CA role to approve entry to final
        if current_user.role != "partner":
            raise HTTPException(
                status_code=403,
                detail="Only Partner/CA role can approve exceptions and finalize accounting vouchers."
            )
        exc.status = "resolved"
        exc.resolved_by_user_id = current_user.id
        exc.resolved_at = datetime.now(timezone.utc)
        exc.resolution_note = "Approved during exception review"
        if exc.entry:
            exc.entry.status = "final"
            exc.entry.approved_by_user_id = current_user.id
            exc.entry.approved_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(exc)

    # Audit log
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action=f"exception_{action}",
        entity_type="exception",
        entity_id=exc.id,
        details={"action": action, "note": action_in.resolution_note}
    )
    db.add(audit)
    db.commit()

    return exc

@router.post("/bulk-action")
def bulk_exception_action(
    bulk_in: BulkExceptionAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    action = bulk_in.action.lower()
    if action == "approve" and current_user.role != "partner":
        raise HTTPException(status_code=403, detail="Only Partner/CA role can bulk approve.")

    exceptions = db.query(ExceptionRecord).filter(
        ExceptionRecord.id.in_(bulk_in.exception_ids),
        ExceptionRecord.organization_id == current_user.organization_id
    ).all()

    updated_count = 0
    for exc in exceptions:
        if action == "assign":
            exc.assigned_to_user_id = bulk_in.assigned_to_user_id
        elif action in ("resolve", "approve"):
            exc.status = "resolved"
            exc.resolved_by_user_id = current_user.id
            exc.resolved_at = datetime.now(timezone.utc)
            exc.resolution_note = bulk_in.resolution_note or f"Bulk {action}"
            if action == "approve" and exc.entry:
                exc.entry.status = "final"
                exc.entry.approved_by_user_id = current_user.id
                exc.entry.approved_at = datetime.now(timezone.utc)
        elif action == "reject":
            exc.status = "rejected"
            exc.resolved_by_user_id = current_user.id
            exc.resolved_at = datetime.now(timezone.utc)
            exc.resolution_note = bulk_in.resolution_note or "Bulk rejected"
        updated_count += 1

    db.commit()
    return {"status": "success", "updated_count": updated_count}
