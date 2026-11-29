import secrets
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Client, FinancialYear, ChartOfAccount, ClientPortalToken, User, ExceptionRecord
from app.schemas import ClientCreate, ClientUpdate, ClientOut
from app.api.deps import get_current_user, require_role
from app.services.categorisation_engine import seed_client_chart_of_accounts
from app.services.compliance_calendar import ComplianceCalendarService

router = APIRouter(prefix="/clients", tags=["Clients"])

@router.get("", response_model=List[ClientOut])
def list_clients(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Strict tenant isolation by organization_id
    clients = db.query(Client).filter(Client.organization_id == current_user.organization_id).all()
    return clients

@router.post("", response_model=ClientOut)
def create_client(
    client_in: ClientCreate,
    current_user: User = Depends(require_role(["partner"])),
    db: Session = Depends(get_db)
):
    client = Client(
        organization_id=current_user.organization_id,
        legal_name=client_in.legal_name.strip(),
        trade_name=client_in.trade_name.strip() if client_in.trade_name else None,
        gstin=client_in.gstin.strip().upper() if client_in.gstin else None,
        pan=client_in.pan.strip().upper() if client_in.pan else None,
        state_code=client_in.state_code.strip(),
        entity_type=client_in.entity_type,
        contact_person=client_in.contact_person,
        contact_email=client_in.contact_email,
        contact_phone=client_in.contact_phone,
    )
    db.add(client)
    db.flush()

    # Create active Financial Year 2024-25
    fy = FinancialYear(
        client_id=client.id,
        year_label="2024-25",
        start_date=datetime(2024, 4, 1, tzinfo=timezone.utc),
        end_date=datetime(2025, 3, 31, 23, 59, 59, tzinfo=timezone.utc),
        is_locked=False
    )
    db.add(fy)

    # Seed sensible Indian Chart of Accounts
    seed_client_chart_of_accounts(db, client)

    db.commit()
    db.refresh(client)
    return client

@router.get("/{client_id}", response_model=ClientOut)
def get_client(
    client_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.organization_id == current_user.organization_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@router.put("/{client_id}", response_model=ClientOut)
def update_client(
    client_id: str,
    client_update: ClientUpdate,
    current_user: User = Depends(require_role(["partner", "article"])),
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.organization_id == current_user.organization_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    update_data = client_update.dict(exclude_unset=True)
    for field, val in update_data.items():
        setattr(client, field, val)

    db.commit()
    db.refresh(client)
    return client

@router.get("/{client_id}/chart-of-accounts")
def get_chart_of_accounts(
    client_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    accounts = db.query(ChartOfAccount).filter(ChartOfAccount.client_id == client_id).all()
    return accounts

@router.get("/{client_id}/compliance-calendar")
def get_compliance_calendar(
    client_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.organization_id == current_user.organization_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    deadlines = ComplianceCalendarService.get_upcoming_deadlines(client_state=client.state_code)
    return deadlines

@router.post("/{client_id}/portal-token")
def create_portal_token(
    client_id: str,
    days_valid: int = 7,
    current_user: User = Depends(require_role(["partner", "article"])),
    db: Session = Depends(get_db)
):
    """Generate secure, expiring token for client direct upload without login."""
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.organization_id == current_user.organization_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    token_str = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=days_valid)

    portal_token = ClientPortalToken(
        client_id=client.id,
        token=token_str,
        expires_at=expires_at,
        created_by_user_id=current_user.id
    )
    db.add(portal_token)
    db.commit()

    return {
        "token": token_str,
        "expires_at": expires_at.isoformat(),
        "portal_url": f"/portal/upload/{token_str}"
    }

@router.post("/{client_id}/missing-doc-reminder")
def draft_missing_doc_reminder(
    client_id: str,
    vendor_name: str,
    period: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.organization_id == current_user.organization_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Generate or reuse portal token
    portal_token = db.query(ClientPortalToken).filter(
        ClientPortalToken.client_id == client.id,
        ClientPortalToken.is_revoked == False,
        ClientPortalToken.expires_at > datetime.now(timezone.utc)
    ).first()

    token_val = portal_token.token if portal_token else "demo-portal-token"
    portal_url = f"https://accuro.firm/portal/upload/{token_val}"

    draft = ComplianceCalendarService.generate_missing_doc_reminders(
        client_name=client.legal_name,
        vendor_name=vendor_name,
        missing_period=period,
        portal_upload_url=portal_url
    )
    return draft
