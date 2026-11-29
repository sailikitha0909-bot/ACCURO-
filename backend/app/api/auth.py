from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    generate_totp_secret, get_totp_uri, verify_totp_code
)
from app.models import User, Organization, AuditLog
from app.schemas import UserLogin, UserRegister, UserOut, Token, TOTPSetupResponse, TOTPVerifyRequest
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email.lower().strip()).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User account is deactivated")

    # If TOTP 2FA is enabled, verify code
    if user.totp_enabled:
        if not login_data.totp_code:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="2FA_REQUIRED"
            )
        if not verify_totp_code(user.totp_secret, login_data.totp_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 2FA TOTP code"
            )

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    # Log login audit
    audit = AuditLog(
        organization_id=user.organization_id,
        user_id=user.id,
        action="user_login",
        entity_type="user",
        entity_id=user.id,
        details={"email": user.email, "role": user.role}
    )
    db.add(audit)
    db.commit()

    token = create_access_token(
        subject=user.id,
        role=user.role,
        org_id=user.organization_id
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/register", response_model=Token)
def register(reg: UserRegister, db: Session = Depends(get_db)):
    # Check if email exists
    existing_user = db.query(User).filter(User.email == reg.email.lower().strip()).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    # Create new CA firm organization
    org = Organization(
        name=reg.organization_name.strip(),
        firm_registration_number=reg.firm_registration_number,
        contact_email=reg.email.lower().strip(),
        settings={"manual_entry_benchmark_mins": 15.0, "retention_years": 8}
    )
    db.add(org)
    db.flush()

    # Create first partner user
    user = User(
        organization_id=org.id,
        email=reg.email.lower().strip(),
        hashed_password=get_password_hash(reg.password),
        full_name=reg.full_name.strip(),
        role="partner", # Creator is Partner/CA
        is_active=True,
        is_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.id, role=user.role, org_id=org.id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/totp/setup", response_model=TOTPSetupResponse)
def setup_totp(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    secret = generate_totp_secret()
    current_user.totp_secret = secret
    db.commit()
    uri = get_totp_uri(secret, current_user.email)
    return {"secret": secret, "qr_uri": uri}

@router.post("/totp/verify")
def verify_totp(data: TOTPVerifyRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="TOTP not initialized")
    if not verify_totp_code(current_user.totp_secret, data.code):
        raise HTTPException(status_code=400, detail="Invalid verification code")
    current_user.totp_enabled = True
    db.commit()
    return {"status": "success", "message": "2FA TOTP successfully enabled"}
