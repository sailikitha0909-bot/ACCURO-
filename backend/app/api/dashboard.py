from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import User
from app.api.deps import get_current_user
from app.services.metrics_service import MetricsService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/metrics")
def get_metrics(
    client_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns live operational metrics computed from the database.
    Strictly zero hardcoded or fake numbers.
    """
    return MetricsService.get_dashboard_metrics(
        db=db,
        organization_id=current_user.organization_id,
        client_id=client_id
    )
