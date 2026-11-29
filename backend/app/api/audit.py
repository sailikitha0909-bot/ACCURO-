from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import AuditLog, User
from app.api.deps import get_current_user

router = APIRouter(prefix="/audit", tags=["Audit Log & DPDP"])

@router.get("")
def list_audit_logs(
    limit: int = 100,
    entity_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog).filter(
        AuditLog.organization_id == current_user.organization_id
    )
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)

    logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
    results = []
    for l in logs:
        user_name = l.user.full_name if l.user else "Accuro AI Engine"
        results.append({
            "id": l.id,
            "timestamp": l.timestamp.isoformat(),
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "user_name": user_name,
            "details": l.details
        })
    return results

@router.get("/compliance/dpdp")
def get_dpdp_compliance_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    India DPDP Act (Digital Personal Data Protection Act) statutory compliance checklist.
    """
    return {
        "encryption_in_transit": "TLS 1.3 / HTTPS",
        "encryption_at_rest": "AES-256 (Fernet) field-level encryption for PAN, GSTIN & Bank accounts",
        "model_training_policy": "STRICT_OFF: No client accounting data is ever used to train AI models",
        "immutable_audit_logging": "Enabled (Every AI extraction, CA edit & approval tracked)",
        "data_retention_policy": "8 Years (Income Tax Act Section 44AA & CGST Act Section 36)",
        "consent_management": "Active per-client consent flag",
        "right_to_erasure_export": "Supported (Full data ZIP export / purge available)"
    }
