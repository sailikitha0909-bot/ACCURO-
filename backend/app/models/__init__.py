import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, BigInteger, Boolean, DateTime, ForeignKey, 
    Text, JSON, Float, Index, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

# -----------------
# 1. Organization (CA Firm)
# -----------------
class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False) # e.g. "Mehta & Associates, Chartered Accountants"
    firm_registration_number = Column(String(50), nullable=True) # FRN e.g. "105642W"
    contact_email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    settings = Column(JSON, default=dict) # Config: manual_entry_benchmark_mins, retention_years, etc.
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    clients = relationship("Client", back_populates="organization", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="organization", cascade="all, delete-orphan")
    entries = relationship("Entry", back_populates="organization", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="organization", cascade="all, delete-orphan")
    exceptions = relationship("ExceptionRecord", back_populates="organization", cascade="all, delete-orphan")
    rules = relationship("CategorisationRule", back_populates="organization", cascade="all, delete-orphan")

# -----------------
# 2. User
# -----------------
class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="article") # "partner" (CA), "article" (Staff), "readonly"
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=True)
    totp_secret = Column(String(64), nullable=True)
    totp_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    organization = relationship("Organization", back_populates="users")
    assigned_exceptions = relationship("ExceptionRecord", back_populates="assignee", foreign_keys="ExceptionRecord.assigned_to_user_id")

# -----------------
# 3. Client (Business under the CA Firm)
# -----------------
class Client(Base):
    __tablename__ = "clients"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    legal_name = Column(String(255), nullable=False) # e.g. "Apex Retailers Private Limited"
    trade_name = Column(String(255), nullable=True)
    gstin = Column(String(50), nullable=True, index=True)
    pan = Column(String(20), nullable=True, index=True)
    state_code = Column(String(5), nullable=False) # e.g. "27" (Maharashtra)
    entity_type = Column(String(50), default="private_limited") # "private_limited", "llp", "proprietorship", "partnership"
    contact_person = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    dpdp_consent = Column(Boolean, default=True)
    retention_period_years = Column(Integer, default=8)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    organization = relationship("Organization", back_populates="clients")
    financial_years = relationship("FinancialYear", back_populates="client", cascade="all, delete-orphan")
    chart_of_accounts = relationship("ChartOfAccount", back_populates="client", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="client", cascade="all, delete-orphan")
    entries = relationship("Entry", back_populates="client", cascade="all, delete-orphan")
    exceptions = relationship("ExceptionRecord", back_populates="client", cascade="all, delete-orphan")
    rules = relationship("CategorisationRule", back_populates="client", cascade="all, delete-orphan")
    portal_tokens = relationship("ClientPortalToken", back_populates="client", cascade="all, delete-orphan")
    gstr2b_records = relationship("GSTR2BRecord", back_populates="client", cascade="all, delete-orphan")
    bank_statements = relationship("BankStatement", back_populates="client", cascade="all, delete-orphan")

# -----------------
# 4. Financial Year
# -----------------
class FinancialYear(Base):
    __tablename__ = "financial_years"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    client_id = Column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    year_label = Column(String(20), nullable=False) # e.g. "2024-25"
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    is_locked = Column(Boolean, default=False)
    locked_at = Column(DateTime(timezone=True), nullable=True)
    locked_by_user_id = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    client = relationship("Client", back_populates="financial_years")
    entries = relationship("Entry", back_populates="financial_year")

# -----------------
# 5. Chart of Accounts
# -----------------
class ChartOfAccount(Base):
    __tablename__ = "chart_of_accounts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    client_id = Column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    account_code = Column(String(50), nullable=False) # e.g. "4010"
    account_name = Column(String(255), nullable=False) # e.g. "Software & SaaS Subscriptions"
    account_type = Column(String(50), nullable=False) # "asset", "liability", "equity", "revenue", "expense"
    parent_group = Column(String(100), nullable=False) # "Indirect Expenses", "Sundry Creditors", etc.
    is_system_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    client = relationship("Client", back_populates="chart_of_accounts")

# -----------------
# 6. Document Intake
# -----------------
class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    financial_year_id = Column(String(36), ForeignKey("financial_years.id", ondelete="SET NULL"), nullable=True, index=True)
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=False) # "pdf", "jpg", "png", "csv", "xlsx"
    file_size_bytes = Column(BigInteger, nullable=False)
    sha256_hash = Column(String(64), nullable=False, index=True) # detect re-uploads immutably
    doc_type = Column(String(50), default="purchase_invoice") # "purchase_invoice", "sales_invoice", "bank_statement", "credit_note", "other"
    status = Column(String(50), default="queued") # "queued", "processing", "needs_attention", "done", "failed"
    uploaded_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    portal_token_id = Column(String(36), ForeignKey("client_portal_tokens.id", ondelete="SET NULL"), nullable=True)
    error_message = Column(Text, nullable=True)
    ocr_raw_text = Column(Text, nullable=True)
    extraction_data = Column(JSON, default=dict) # Strict JSON schema with confidence & bbox
    created_at = Column(DateTime(timezone=True), default=utc_now)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    organization = relationship("Organization", back_populates="documents")
    client = relationship("Client", back_populates="documents")
    entry = relationship("Entry", back_populates="document", uselist=False)
    exceptions = relationship("ExceptionRecord", back_populates="document", cascade="all, delete-orphan")

# -----------------
# 7. Accounting Entry (Draft & Final)
# -----------------
class Entry(Base):
    __tablename__ = "entries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    financial_year_id = Column(String(36), ForeignKey("financial_years.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, unique=True)

    entry_type = Column(String(50), default="purchase") # "purchase", "sales", "journal", "payment", "receipt"
    voucher_number = Column(String(100), nullable=True)
    invoice_number = Column(String(100), nullable=False, index=True)
    invoice_date = Column(DateTime(timezone=True), nullable=False)
    party_name = Column(String(255), nullable=False, index=True)
    party_gstin = Column(String(50), nullable=True, index=True)
    place_of_supply = Column(String(5), nullable=False) # e.g. "27"
    reverse_charge = Column(Boolean, default=False)
    
    # Monetary values stored strictly as integer paise (1 Rupee = 100 Paise)
    taxable_value_paise = Column(BigInteger, default=0, nullable=False)
    cgst_paise = Column(BigInteger, default=0, nullable=False)
    sgst_paise = Column(BigInteger, default=0, nullable=False)
    igst_paise = Column(BigInteger, default=0, nullable=False)
    cess_paise = Column(BigInteger, default=0, nullable=False)
    round_off_paise = Column(BigInteger, default=0, nullable=False)
    total_amount_paise = Column(BigInteger, default=0, nullable=False)

    # TDS
    tds_section = Column(String(50), nullable=True) # e.g. "194C", "194J"
    tds_rate = Column(Float, nullable=True) # e.g. 10.0, 2.0
    tds_amount_paise = Column(BigInteger, default=0)

    # Line items with HSN/SAC, rates, and debit ledgers
    line_items = Column(JSON, default=list)

    # Primary Ledger Accounts
    debit_account_id = Column(String(36), ForeignKey("chart_of_accounts.id", ondelete="SET NULL"), nullable=True)
    credit_account_id = Column(String(36), ForeignKey("chart_of_accounts.id", ondelete="SET NULL"), nullable=True)

    # Workflow Status: "draft" (AI created), "in_review", "final" (CA approved), "rejected"
    status = Column(String(50), default="draft", index=True)
    is_itc_eligible = Column(Boolean, default=True)
    itc_blocked_reason = Column(String(255), nullable=True) # Section 17(5) reason
    
    # Partner/CA Approval tracking
    approved_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    organization = relationship("Organization", back_populates="entries")
    client = relationship("Client", back_populates="entries")
    financial_year = relationship("FinancialYear", back_populates="entries")
    document = relationship("Document", back_populates="entry")
    debit_account = relationship("ChartOfAccount", foreign_keys=[debit_account_id])
    credit_account = relationship("ChartOfAccount", foreign_keys=[credit_account_id])
    approver = relationship("User", foreign_keys=[approved_by_user_id])
    exceptions = relationship("ExceptionRecord", back_populates="entry", cascade="all, delete-orphan")

# -----------------
# 8. Exception Record (Primary CA Review Queue)
# -----------------
class ExceptionRecord(Base):
    __tablename__ = "exceptions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True)
    entry_id = Column(String(36), ForeignKey("entries.id", ondelete="SET NULL"), nullable=True, index=True)

    severity = Column(String(20), nullable=False, index=True) # "high", "medium", "low"
    exception_type = Column(String(50), nullable=False, index=True)
    # Types: gstin_invalid, tax_type_mismatch, arithmetic_error, hsn_rate_mismatch,
    #        duplicate_invoice, time_barred_16_4, blocked_credit_17_5, missing_mandatory_field,
    #        unusual_amount, gstr2b_mismatch, bank_unmatched, rule_conflict
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False) # Calm, professional Indian tax explanation
    evidence = Column(JSON, default=dict) # source doc value, rule value, bounding box
    suggested_fix = Column(Text, nullable=True)

    status = Column(String(50), default="open", index=True) # "open", "in_review", "resolved", "rejected"
    assigned_to_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    resolved_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_note = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now)

    organization = relationship("Organization", back_populates="exceptions")
    client = relationship("Client", back_populates="exceptions")
    document = relationship("Document", back_populates="exceptions")
    entry = relationship("Entry", back_populates="exceptions")
    assignee = relationship("User", foreign_keys=[assigned_to_user_id], back_populates="assigned_exceptions")

# -----------------
# 9. Categorisation Rules (Learned from CA actions)
# -----------------
class CategorisationRule(Base):
    __tablename__ = "categorisation_rules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    
    rule_type = Column(String(50), nullable=False) # "vendor_exact", "vendor_keyword", "hsn_code", "description_keyword"
    match_pattern = Column(String(255), nullable=False) # e.g. "Amazon Web Services", "9983", "Reliance Jio"
    target_account_id = Column(String(36), ForeignKey("chart_of_accounts.id", ondelete="CASCADE"), nullable=False)
    confidence = Column(Float, default=1.0)
    source = Column(String(50), default="learned_ca_correction") # "learned_ca_correction", "manual_rule", "default_template"
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    organization = relationship("Organization", back_populates="rules")
    client = relationship("Client", back_populates="rules")
    target_account = relationship("ChartOfAccount")

# -----------------
# 10. GSTR-2B Records
# -----------------
class GSTR2BRecord(Base):
    __tablename__ = "gstr2b_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    return_period = Column(String(20), nullable=False, index=True) # e.g. "072024" or "2024-07"
    supplier_gstin = Column(String(50), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=True)
    invoice_number = Column(String(100), nullable=False, index=True)
    invoice_date = Column(DateTime(timezone=True), nullable=False)
    invoice_type = Column(String(20), default="R")
    
    taxable_value_paise = Column(BigInteger, default=0, nullable=False)
    igst_paise = Column(BigInteger, default=0, nullable=False)
    cgst_paise = Column(BigInteger, default=0, nullable=False)
    sgst_paise = Column(BigInteger, default=0, nullable=False)
    cess_paise = Column(BigInteger, default=0, nullable=False)
    
    itc_availability = Column(String(10), default="Y") # "Y" or "N"
    itc_reason = Column(String(255), nullable=True)
    
    reconciliation_status = Column(String(50), default="gstr2b_only", index=True) 
    # "matched", "partially_matched", "books_only", "gstr2b_only", "duplicate"
    matched_entry_id = Column(String(36), ForeignKey("entries.id", ondelete="SET NULL"), nullable=True)
    match_score = Column(Float, nullable=True)
    match_discrepancies = Column(JSON, default=dict)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)

    client = relationship("Client", back_populates="gstr2b_records")
    matched_entry = relationship("Entry")

# -----------------
# 11. Bank Statements & Lines
# -----------------
class BankStatement(Base):
    __tablename__ = "bank_statements"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    bank_name = Column(String(100), nullable=False) # e.g. "HDFC Bank", "ICICI Bank"
    account_number_masked = Column(String(50), nullable=False)
    statement_period = Column(String(50), nullable=True) # e.g. "April 2024"
    uploaded_at = Column(DateTime(timezone=True), default=utc_now)

    client = relationship("Client", back_populates="bank_statements")
    lines = relationship("BankStatementLine", back_populates="statement", cascade="all, delete-orphan")

class BankStatementLine(Base):
    __tablename__ = "bank_statement_lines"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    statement_id = Column(String(36), ForeignKey("bank_statements.id", ondelete="CASCADE"), nullable=False, index=True)
    txn_date = Column(DateTime(timezone=True), nullable=False)
    value_date = Column(DateTime(timezone=True), nullable=True)
    narration = Column(Text, nullable=False)
    reference_no = Column(String(100), nullable=True, index=True) # UTR or Cheque
    debit_paise = Column(BigInteger, default=0, nullable=False)
    credit_paise = Column(BigInteger, default=0, nullable=False)
    balance_paise = Column(BigInteger, default=0, nullable=False)
    
    reconciliation_status = Column(String(50), default="unmatched", index=True) # "matched", "unmatched"
    matched_entry_id = Column(String(36), ForeignKey("entries.id", ondelete="SET NULL"), nullable=True)
    match_reason = Column(String(255), nullable=True)

    statement = relationship("BankStatement", back_populates="lines")
    matched_entry = relationship("Entry")

# -----------------
# 12. Immutable Audit Log
# -----------------
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False) # "ai_extraction", "entry_created", "entry_approved", "entry_rejected", "tally_export", "login"
    entity_type = Column(String(50), nullable=False) # "document", "entry", "exception", "rule", "client"
    entity_id = Column(String(36), nullable=False, index=True)
    details = Column(JSON, default=dict) # Immutable snapshot: before, after, changes, ip_address, user_agent
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)

    organization = relationship("Organization", back_populates="audit_logs")
    user = relationship("User")

# -----------------
# 13. Client Portal Token (Secure External Upload)
# -----------------
class ClientPortalToken(Base):
    __tablename__ = "client_portal_tokens"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    client_id = Column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(64), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_revoked = Column(Boolean, default=False)
    upload_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    client = relationship("Client", back_populates="portal_tokens")
