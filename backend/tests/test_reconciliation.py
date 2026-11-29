from datetime import datetime, timezone
from app.services.reconciliation_engine import normalize_invoice_number, ReconciliationEngine
from app.models import Entry, GSTR2BRecord, BankStatement, BankStatementLine, Client, Organization, FinancialYear

def test_invoice_number_normalization():
    # Test stripping slashes, dashes, spaces, and leading zeros
    assert normalize_invoice_number("INV/2024-25/0014") == "INV20242514"
    assert normalize_invoice_number("inv-2024-25-14") == "INV20242514"
    assert normalize_invoice_number("  0009981  ") == "9981"
    assert normalize_invoice_number("GST_MUM_0045") == "GSTMUM45"

def test_gstr2b_reconciliation_exact_and_partial(db_session):
    org = Organization(name="Test CA", contact_email="ca@test.in")
    db_session.add(org)
    db_session.flush()

    client = Client(organization_id=org.id, legal_name="Apex Test", state_code="27")
    db_session.add(client)
    db_session.flush()

    fy = FinancialYear(client_id=client.id, year_label="2024-25", start_date=datetime(2024,4,1,tzinfo=timezone.utc), end_date=datetime(2025,3,31,tzinfo=timezone.utc))
    db_session.add(fy)
    db_session.flush()

    # 1. Exact Match Entry
    entry_exact = Entry(
        organization_id=org.id,
        client_id=client.id,
        financial_year_id=fy.id,
        entry_type="purchase",
        invoice_number="INV/2024/101",
        invoice_date=datetime(2024, 7, 5, tzinfo=timezone.utc),
        party_name="AWS India",
        party_gstin="07AABCA1234F1Z5",
        place_of_supply="27",
        taxable_value_paise=1000000,
        cgst_paise=0,
        sgst_paise=0,
        igst_paise=180000,
        total_amount_paise=1180000,
        status="final"
    )

    # 2. In Books Not in 2B Entry (Vendor hasn't filed GSTR-1)
    entry_unfiled = Entry(
        organization_id=org.id,
        client_id=client.id,
        financial_year_id=fy.id,
        entry_type="purchase",
        invoice_number="UNFILED-777",
        invoice_date=datetime(2024, 7, 12, tzinfo=timezone.utc),
        party_name="Late Vendor Pvt Ltd",
        party_gstin="27AABCL8899K1Z4",
        place_of_supply="27",
        taxable_value_paise=500000,
        cgst_paise=45000,
        sgst_paise=45000,
        igst_paise=0,
        total_amount_paise=590000,
        status="final"
    )

    db_session.add_all([entry_exact, entry_unfiled])
    db_session.flush()

    # Corresponding GSTR-2B Records
    rec_exact = GSTR2BRecord(
        organization_id=org.id,
        client_id=client.id,
        return_period="072024",
        supplier_gstin="07AABCA1234F1Z5",
        supplier_name="AWS India",
        invoice_number="INV-2024-101", # Normalized matches INV/2024/101!
        invoice_date=datetime(2024, 7, 5, tzinfo=timezone.utc),
        taxable_value_paise=1000000,
        igst_paise=180000,
        cgst_paise=0,
        sgst_paise=0,
        cess_paise=0,
        itc_availability="Y"
    )

    # In 2B Not in Books Record
    rec_unclaimed = GSTR2BRecord(
        organization_id=org.id,
        client_id=client.id,
        return_period="072024",
        supplier_gstin="27AABCU1122M1Z0",
        supplier_name="Unclaimed Vendor Ltd",
        invoice_number="UNCLAIMED-009",
        invoice_date=datetime(2024, 7, 20, tzinfo=timezone.utc),
        taxable_value_paise=200000,
        igst_paise=0,
        cgst_paise=18000,
        sgst_paise=18000,
        cess_paise=0,
        itc_availability="Y"
    )

    db_session.add_all([rec_exact, rec_unclaimed])
    db_session.commit()

    result = ReconciliationEngine.match_books_with_gstr2b(
        db=db_session,
        client_id=client.id,
        return_period="072024"
    )

    assert result["matched_count"] == 1
    assert result["books_only_count"] == 1
    assert result["gstr2b_only_count"] == 1
    assert result["itc_summary"]["eligible_itc_paise"] == 180000
    assert result["itc_summary"]["at_risk_itc_paise"] == 90000 # unfiled vendor credit at risk
    assert len(result["vendor_followups"]) == 1
    assert result["vendor_followups"][0]["supplier_name"] == "Late Vendor Pvt Ltd"
