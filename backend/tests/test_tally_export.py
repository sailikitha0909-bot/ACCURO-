from datetime import datetime, timezone
from app.services.export_service import ExportService
from app.models import Entry

def test_tally_prime_xml_generation():
    class MockAccount:
        def __init__(self, name):
            self.account_name = name

    class MockEntry:
        def __init__(self):
            self.invoice_number = "INV-2024-88421"
            self.invoice_date = datetime(2024, 7, 5, tzinfo=timezone.utc)
            self.party_name = "Amazon Web Services India Private Limited"
            self.party_gstin = "07AABCA1234F1Z5"
            self.entry_type = "purchase"
            self.taxable_value_paise = 4500000 # ₹45,000.00
            self.cgst_paise = 0
            self.sgst_paise = 0
            self.igst_paise = 810000          # ₹8,100.00
            self.round_off_paise = 0
            self.total_amount_paise = 5310000  # ₹53,100.00
            self.debit_account = MockAccount("Software & SaaS Subscriptions")

    entries = [MockEntry()]
    xml_output = ExportService.generate_tally_xml(entries, company_name="Apex Retailers Pvt Ltd")

    # Verify Tally Prime XML structure
    assert "<ENVELOPE>" in xml_output
    assert "<TALLYREQUEST>Import Data</TALLYREQUEST>" in xml_output
    assert "<REPORTNAME>Vouchers</REPORTNAME>" in xml_output
    assert '<VOUCHER VCHTYPE="Purchase" ACTION="Create"' in xml_output
    assert "<VOUCHERNUMBER>INV-2024-88421</VOUCHERNUMBER>" in xml_output
    assert "<PARTYLEDGERNAME>Amazon Web Services India Private Limited</PARTYLEDGERNAME>" in xml_output
    assert "<LEDGERNAME>Software &amp; SaaS Subscriptions</LEDGERNAME>" in xml_output or "<LEDGERNAME>Software & SaaS Subscriptions</LEDGERNAME>" in xml_output
    assert "<LEDGERNAME>Input IGST</LEDGERNAME>" in xml_output
    assert "<AMOUNT>53100.00</AMOUNT>" in xml_output
    assert "<AMOUNT>-45000.00</AMOUNT>" in xml_output
    assert "<AMOUNT>-8100.00</AMOUNT>" in xml_output
    assert "AI-prepared draft by Accuro. Requires CA review." in xml_output
