import base64
import hashlib
from cryptography.fernet import Fernet
from app.core.config import settings

def _get_fernet() -> Fernet:
    # Derive 32-byte key from secret
    derived = hashlib.sha256(settings.DPDP_FIELD_ENCRYPTION_KEY.encode()).digest()
    key_b64 = base64.urlsafe_b64encode(derived)
    return Fernet(key_b64)

def encrypt_sensitive_field(value: str | None) -> str | None:
    """Field-level encryption for sensitive Indian business data (PAN, Bank Account, Aadhaar)."""
    if not value:
        return value
    f = _get_fernet()
    encrypted = f.encrypt(value.encode('utf-8'))
    return encrypted.decode('utf-8')

def decrypt_sensitive_field(encrypted_value: str | None) -> str | None:
    """Decrypt field-level encrypted values."""
    if not encrypted_value:
        return encrypted_value
    try:
        f = _get_fernet()
        decrypted = f.decrypt(encrypted_value.encode('utf-8'))
        return decrypted.decode('utf-8')
    except Exception:
        # If already plain text (e.g. legacy/testing)
        return encrypted_value

def mask_gstin(gstin: str | None) -> str:
    """Mask GSTIN for display: 27AABCA****1Z5"""
    if not gstin or len(gstin) < 15:
        return gstin or ""
    return f"{gstin[:7]}****{gstin[-3:]}"

def mask_pan(pan: str | None) -> str:
    """Mask PAN for display: ABCDE****F"""
    if not pan or len(pan) < 10:
        return pan or ""
    return f"{pan[:5]}****{pan[-1]}"

def mask_bank_account(account_number: str | None) -> str:
    """Mask Bank Account for display: **********1234"""
    if not account_number or len(account_number) < 4:
        return account_number or ""
    return f"{'*' * (len(account_number) - 4)}{account_number[-4:]}"
