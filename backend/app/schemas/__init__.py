from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr

# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: "UserOut"

class TokenPayload(BaseModel):
    sub: str
    role: str
    org_id: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    totp_code: Optional[str] = None

class UserRegister(BaseModel):
    organization_name: str
    firm_registration_number: Optional[str] = None
    email: EmailStr
    full_name: str
    password: str
    role: Optional[str] = "partner" # Partner by default for account creator

class UserOut(BaseModel):
    id: str
    organization_id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    totp_enabled: bool

    class Config:
        from_attributes = True

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class TOTPSetupResponse(BaseModel):
    secret: str
    qr_uri: str

class TOTPVerifyRequest(BaseModel):
    code: str

# Client Schemas
class ClientCreate(BaseModel):
    legal_name: str
    trade_name: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    state_code: str
    entity_type: Optional[str] = "private_limited"
    contact_person: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None

class ClientUpdate(BaseModel):
    legal_name: Optional[str] = None
    trade_name: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    state_code: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    is_active: Optional[bool] = None

class FinancialYearOut(BaseModel):
    id: str
    year_label: str
    start_date: datetime
    end_date: datetime
    is_locked: bool

    class Config:
        from_attributes = True

class ClientOut(BaseModel):
    id: str
    organization_id: str
    legal_name: str
    trade_name: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    state_code: str
    entity_type: str
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_active: bool
    financial_years: List[FinancialYearOut] = []

    class Config:
        from_attributes = True

# Document Schemas
class DocumentOut(BaseModel):
    id: str
    client_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    sha256_hash: str
    doc_type: str
    status: str
    error_message: Optional[str] = None
    extraction_data: Optional[dict] = None
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Entry Schemas
class EntryOut(BaseModel):
    id: str
    organization_id: str
    client_id: str
    document_id: Optional[str] = None
    entry_type: str
    voucher_number: Optional[str] = None
    invoice_number: str
    invoice_date: datetime
    party_name: str
    party_gstin: Optional[str] = None
    place_of_supply: str
    reverse_charge: bool
    taxable_value_paise: int
    cgst_paise: int
    sgst_paise: int
    igst_paise: int
    cess_paise: int
    round_off_paise: int
    total_amount_paise: int
    line_items: List[dict] = []
    debit_account_id: Optional[str] = None
    credit_account_id: Optional[str] = None
    status: str
    is_itc_eligible: bool
    itc_blocked_reason: Optional[str] = None
    approved_by_user_id: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class EntryUpdate(BaseModel):
    invoice_number: Optional[str] = None
    invoice_date: Optional[datetime] = None
    party_name: Optional[str] = None
    party_gstin: Optional[str] = None
    place_of_supply: Optional[str] = None
    taxable_value_paise: Optional[int] = None
    cgst_paise: Optional[int] = None
    sgst_paise: Optional[int] = None
    igst_paise: Optional[int] = None
    cess_paise: Optional[int] = None
    round_off_paise: Optional[int] = None
    total_amount_paise: Optional[int] = None
    debit_account_id: Optional[str] = None
    is_itc_eligible: Optional[bool] = None
    itc_blocked_reason: Optional[str] = None
    line_items: Optional[List[dict]] = None

# Exception Schemas
class ExceptionOut(BaseModel):
    id: str
    organization_id: str
    client_id: str
    document_id: Optional[str] = None
    entry_id: Optional[str] = None
    severity: str
    exception_type: str
    title: str
    description: str
    evidence: dict = {}
    suggested_fix: Optional[str] = None
    status: str
    assigned_to_user_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ExceptionAction(BaseModel):
    action: str # "approve", "resolve", "reject", "assign"
    assigned_to_user_id: Optional[str] = None
    resolution_note: Optional[str] = None

class BulkExceptionAction(BaseModel):
    exception_ids: List[str]
    action: str
    assigned_to_user_id: Optional[str] = None
    resolution_note: Optional[str] = None

# Rule Schemas
class RuleCreate(BaseModel):
    client_id: str
    rule_type: str
    match_pattern: str
    target_account_id: str

class RuleOut(BaseModel):
    id: str
    client_id: str
    rule_type: str
    match_pattern: str
    target_account_id: str
    confidence: float
    source: str
    usage_count: int

    class Config:
        from_attributes = True
