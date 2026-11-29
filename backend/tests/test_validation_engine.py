from datetime import datetime, timezone, timedelta
from app.services.validation_engine import (
    validate_gstin_checksum, calculate_gstin_checksum_char,
    ValidationEngine, ValidationIssue
)

def test_gstin_checksum_validation():
    # Valid Indian GSTINs with accurate Mod-36 checksum
    valid_gstin1 = "27AABCA1234F1Z" + calculate_gstin_checksum_char("27AABCA1234F1Z")
    valid_gstin2 = "29AABCZ9876K1Z" + calculate_gstin_checksum_char("29AABCZ9876K1Z")
    valid_gstin3 = "07AAACB5555L1Z" + calculate_gstin_checksum_char("07AAACB5555L1Z")

    assert validate_gstin_checksum(valid_gstin1) == True
    assert validate_gstin_checksum(valid_gstin2) == True
    assert validate_gstin_checksum(valid_gstin3) == True

    # Invalid GSTINs
    invalid_char = "X" if valid_gstin1[-1] != "X" else "Y"
    assert validate_gstin_checksum(valid_gstin1[:-1] + invalid_char) == False # Wrong check digit
    assert validate_gstin_checksum("99AABCA1234F1Z5") == False # Invalid state code
    assert validate_gstin_checksum("INVALID_GSTIN") == False
    assert validate_gstin_checksum("") == False

def test_tax_logic_intra_vs_inter_state():
    fy_start = datetime(2024, 4, 1, tzinfo=timezone.utc)
    fy_end = datetime(2025, 3, 31, tzinfo=timezone.utc)

    # 1. Intra-State Supply with Wrong Tax (IGST charged instead of CGST/SGST)
    entry_intra_wrong = {
        "invoice_number": "INV-001",
        "invoice_date": datetime(2024, 7, 10, tzinfo=timezone.utc),
        "party_name": "Local Supplier MH",
        "party_gstin": "27AABCA1234F1Z5", # State 27
        "place_of_supply": "27",          # POS 27 -> Intra-state
        "taxable_value_paise": 1000000,
        "cgst_paise": 0,
        "sgst_paise": 0,
        "igst_paise": 180000,             # Wrong! Should be CGST + SGST
        "cess_paise": 0,
        "total_amount_paise": 1180000
    }
    issues = ValidationEngine.validate_entry(entry_intra_wrong, client_state_code="27", fy_start_date=fy_start, fy_end_date=fy_end)
    issue_types = [i.exception_type for i in issues]
    assert "tax_type_mismatch" in issue_types
    tax_issue = next(i for i in issues if i.exception_type == "tax_type_mismatch")
    assert tax_issue.severity == "high"
    assert "IGST Charged on Intra-State Supply" in tax_issue.title

    # 2. Inter-State Supply with Wrong Tax (CGST/SGST charged instead of IGST)
    entry_inter_wrong = {
        "invoice_number": "INV-002",
        "invoice_date": datetime(2024, 7, 10, tzinfo=timezone.utc),
        "party_name": "Delhi Supplier",
        "party_gstin": "07AAACB5555L1Z8", # State 07
        "place_of_supply": "27",          # POS 27 -> Inter-state
        "taxable_value_paise": 1000000,
        "cgst_paise": 90000,              # Wrong! Should be IGST
        "sgst_paise": 90000,
        "igst_paise": 0,
        "cess_paise": 0,
        "total_amount_paise": 1180000
    }
    issues2 = ValidationEngine.validate_entry(entry_inter_wrong, client_state_code="27", fy_start_date=fy_start, fy_end_date=fy_end)
    assert any(i.exception_type == "tax_type_mismatch" and "CGST/SGST Charged on Inter-State Supply" in i.title for i in issues2)

def test_arithmetic_checks():
    fy_start = datetime(2024, 4, 1, tzinfo=timezone.utc)
    fy_end = datetime(2025, 3, 31, tzinfo=timezone.utc)

    # Header mismatch
    entry_bad_math = {
        "invoice_number": "INV-003",
        "invoice_date": datetime(2024, 7, 10, tzinfo=timezone.utc),
        "party_name": "Supplier X",
        "party_gstin": "27AABCA1234F1Z5",
        "place_of_supply": "27",
        "taxable_value_paise": 1000000, # ₹10,000
        "cgst_paise": 90000,           # ₹900
        "sgst_paise": 90000,           # ₹900
        "igst_paise": 0,
        "total_amount_paise": 1500000  # Stated ₹15,000 instead of ₹11,800!
    }
    issues = ValidationEngine.validate_entry(entry_bad_math, client_state_code="27", fy_start_date=fy_start, fy_end_date=fy_end)
    assert any(i.exception_type == "arithmetic_error" for i in issues)

def test_section_17_5_blocked_credit_detection():
    fy_start = datetime(2024, 4, 1, tzinfo=timezone.utc)
    fy_end = datetime(2025, 3, 31, tzinfo=timezone.utc)

    catering_entry = {
        "invoice_number": "INV-CAT-01",
        "invoice_date": datetime(2024, 7, 10, tzinfo=timezone.utc),
        "party_name": "Royal Banquet & Outdoor Catering",
        "party_gstin": "27AABCA1234F1Z5",
        "place_of_supply": "27",
        "taxable_value_paise": 2000000,
        "cgst_paise": 50000,
        "sgst_paise": 50000,
        "igst_paise": 0,
        "total_amount_paise": 2100000,
        "line_items": [{"description": "Executive Client Lunch Buffet", "hsn_sac": "9963", "gst_rate": 5.0, "taxable_paise": 2000000}]
    }
    issues = ValidationEngine.validate_entry(catering_entry, client_state_code="27", fy_start_date=fy_start, fy_end_date=fy_end)
    assert any(i.exception_type == "blocked_credit_17_5" for i in issues)

def test_duplicate_detection():
    fy_start = datetime(2024, 4, 1, tzinfo=timezone.utc)
    fy_end = datetime(2025, 3, 31, tzinfo=timezone.utc)

    past_entries = [{
        "id": "entry-existing-1",
        "invoice_number": "INV-2024-99",
        "party_gstin": "27AABCA1234F1Z5",
        "total_amount_paise": 5000000,
        "invoice_date": "2024-07-15T00:00:00+00:00"
    }]

    # Re-uploaded invoice with same invoice number & supplier
    duplicate_entry = {
        "id": "new-entry-2",
        "invoice_number": "INV-2024-99",
        "invoice_date": datetime(2024, 7, 15, tzinfo=timezone.utc),
        "party_name": "Test Supplier",
        "party_gstin": "27AABCA1234F1Z5",
        "place_of_supply": "27",
        "taxable_value_paise": 4237288,
        "cgst_paise": 381356,
        "sgst_paise": 381356,
        "igst_paise": 0,
        "total_amount_paise": 5000000
    }
    issues = ValidationEngine.validate_entry(duplicate_entry, client_state_code="27", fy_start_date=fy_start, fy_end_date=fy_end, existing_entries=past_entries)
    assert any(i.exception_type == "duplicate_invoice" and "Exact Duplicate" in i.title for i in issues)
