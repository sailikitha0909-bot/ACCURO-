import os
import random
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models import (
    Organization, User, Client, FinancialYear, ChartOfAccount,
    Document, Entry, ExceptionRecord, CategorisationRule,
    GSTR2BRecord, BankStatement, BankStatementLine, AuditLog, ClientPortalToken
)
from app.services.validation_engine import (
    calculate_gstin_checksum_char, ValidationEngine
)
from app.services.categorisation_engine import seed_client_chart_of_accounts

def generate_valid_gstin(state_code: str, pan_alpha: str, pan_num: str, entity_num: str = "1") -> str:
    """Constructs a 100% valid GSTIN with correct Luhn Mod-36 checksum."""
    first_14 = f"{state_code}{pan_alpha}{pan_num}{pan_alpha[0]}{entity_num}Z"
    check_char = calculate_gstin_checksum_char(first_14)
    return f"{first_14}{check_char}"

def seed_database():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # Check if already seeded
        existing_org = db.query(Organization).filter(Organization.contact_email == "partner@mehta-ca.in").first()
        if existing_org:
            print("Database already seeded with demo CA firm. Skipping.")
            return

        print("Seeding Accuro with production-grade CA firm demo data...")

        # 1. Organization: Mehta & Associates, Chartered Accountants
        org = Organization(
            name="Mehta & Associates, Chartered Accountants",
            firm_registration_number="105642W",
            contact_email="partner@mehta-ca.in",
            phone="+91 22 2654 8800",
            address="Floor 4, Nariman Point Commercial Hub, Mumbai, Maharashtra 400021",
            settings={
                "manual_entry_benchmark_mins": 15.0,
                "retention_years": 8,
                "auto_reconcile_tolerance_paise": 500,
            }
        )
        db.add(org)
        db.flush()

        # 2. Users: Partner (CA) and Article (Staff)
        partner_user = User(
            organization_id=org.id,
            email="partner@mehta-ca.in",
            hashed_password=get_password_hash("Partner@Accuro2025!"),
            full_name="CA Rajesh Mehta, FCA",
            role="partner", # Can approve, finalise, export
            is_active=True,
            is_verified=True,
            totp_enabled=False
        )
        article_user = User(
            organization_id=org.id,
            email="article@mehta-ca.in",
            hashed_password=get_password_hash("Article@Accuro2025!"),
            full_name="Pooja Sharma (Article Assistant)",
            role="article", # Can review, edit, draft; cannot finalise
            is_active=True,
            is_verified=True,
            totp_enabled=False
        )
        db.add_all([partner_user, article_user])
        db.flush()

        # 3. Clients: 3 realistic Indian businesses
        client_configs = [
            {
                "legal_name": "Apex Retailers Private Limited",
                "trade_name": "Apex Mart",
                "gstin": generate_valid_gstin("27", "AABCA", "1234"),
                "pan": "AABCA1234A",
                "state_code": "27", # Maharashtra
                "entity_type": "private_limited",
                "contact_person": "Vikram Malhotra",
                "contact_email": "accounts@apexretail.in",
            },
            {
                "legal_name": "Zenith Technologies LLP",
                "trade_name": "Zenith Cloud Solutions",
                "gstin": generate_valid_gstin("29", "AABCZ", "9876"),
                "pan": "AABCZ9876A",
                "state_code": "29", # Karnataka
                "entity_type": "llp",
                "contact_person": "Ananya Rao",
                "contact_email": "finance@zenithtech.io",
            },
            {
                "legal_name": "Bharat Logistics & Freight Solutions",
                "trade_name": "Bharat Cargo",
                "gstin": generate_valid_gstin("07", "AAACB", "5555"),
                "pan": "AAACB5555A",
                "state_code": "07", # Delhi
                "entity_type": "partnership",
                "contact_person": "Harpreet Singh",
                "contact_email": "harpreet@bharatcargo.co.in",
            }
        ]

        clients = []
        for c_data in client_configs:
            client = Client(
                organization_id=org.id,
                legal_name=c_data["legal_name"],
                trade_name=c_data["trade_name"],
                gstin=c_data["gstin"],
                pan=c_data["pan"],
                state_code=c_data["state_code"],
                entity_type=c_data["entity_type"],
                contact_person=c_data["contact_person"],
                contact_email=c_data["contact_email"],
            )
            db.add(client)
            db.flush()

            # Active Financial Year 2024-25
            fy = FinancialYear(
                client_id=client.id,
                year_label="2024-25",
                start_date=datetime(2024, 4, 1, tzinfo=timezone.utc),
                end_date=datetime(2025, 3, 31, 23, 59, 59, tzinfo=timezone.utc),
                is_locked=False
            )
            db.add(fy)
            db.flush()

            # Chart of accounts
            accounts = seed_client_chart_of_accounts(db, client)
            client._accounts = {acc.account_code: acc for acc in accounts}
            client._fy = fy

            # Client Portal Token
            p_token = ClientPortalToken(
                client_id=client.id,
                token=f"demo-token-{client.id[:8]}",
                expires_at=datetime.now(timezone.utc) + timedelta(days=90),
                created_by_user_id=partner_user.id
            )
            db.add(p_token)

            clients.append(client)

        db.flush()

        # 4. Realistic Vendors Schedule
        vendors = [
            {"name": "Amazon Web Services India Pvt Ltd", "state": "07", "pan": "AABCA", "pan_num": "4411", "hsn": "9983", "rate": 18.0, "acc": "4010", "item": "Cloud Compute & Hosting Services", "base_paise": 4500000},
            {"name": "Reliance Jio Infocomm Limited", "state": "27", "pan": "AAACR", "pan_num": "5055", "hsn": "9984", "rate": 18.0, "acc": "4050", "item": "High Speed Corporate Leased Line", "base_paise": 1250000},
            {"name": "Tata Communications Limited", "state": "27", "pan": "AAACT", "pan_num": "2299", "hsn": "9984", "rate": 18.0, "acc": "4050", "item": "SIP Trunk & Cloud Telephony", "base_paise": 850000},
            {"name": "Google India Digital Services Pvt Ltd", "state": "29", "pan": "AABCG", "pan_num": "1188", "hsn": "9983", "rate": 18.0, "acc": "4010", "item": "Google Workspace Enterprise Licences", "base_paise": 3200000},
            {"name": "Zoho Corporation Private Limited", "state": "33", "pan": "AABCZ", "pan_num": "3344", "hsn": "9973", "rate": 18.0, "acc": "4010", "item": "Zoho One Subscription Renewal", "base_paise": 2800000},
            {"name": "Office Needs Hub Private Limited", "state": "27", "pan": "AABCO", "pan_num": "7722", "hsn": "4820", "rate": 18.0, "acc": "4060", "item": "A4 Paper Reams & Office Consumables", "base_paise": 450000},
            {"name": "Shree Ganesh Logistics & Freight", "state": "24", "pan": "AABCS", "pan_num": "6633", "hsn": "9965", "rate": 5.0, "acc": "4090", "item": "Inter-State Freight & Delivery Charges", "base_paise": 6800000},
            {"name": "Dell India Private Limited", "state": "29", "pan": "AABCD", "pan_num": "8822", "hsn": "8471", "rate": 18.0, "acc": "1210", "item": "Latitude Laptops & Docking Stations", "base_paise": 18500000},
            {"name": "Godrej Interio Facility Supplies", "state": "27", "pan": "AAACG", "pan_num": "9911", "hsn": "9403", "rate": 18.0, "acc": "1220", "item": "Ergonomic Mesh Chairs & Workstations", "base_paise": 9200000},
            {"name": "KPMG India Tax Advisors LLP", "state": "27", "pan": "AABCK", "pan_num": "1122", "hsn": "9982", "rate": 18.0, "acc": "4020", "item": "Statutory Transfer Pricing Advisory", "base_paise": 15000000},
        ]

        # Generate ~100 realistic invoices across the 3 clients
        print("Generating ~100 invoices with valid GSTINs, mixed rates and deliberate exception cases...")
        invoice_counter = 1001
        all_created_entries = []

        for client_idx, client in enumerate(clients):
            # Target ~35 invoices per client
            for i in range(34):
                v = random.choice(vendors)
                supplier_gstin = generate_valid_gstin(v["state"], v["pan"], v["pan_num"])
                inv_num = f"INV/24-25/{invoice_counter}"
                invoice_counter += 1

                # Dates spread across April 2024 to September 2024
                days_offset = random.randint(15, 150)
                inv_date = datetime(2024, 4, 1, tzinfo=timezone.utc) + timedelta(days=days_offset)

                taxable_p = v["base_paise"] + random.randint(-200000, 500000)
                taxable_p = max(100000, taxable_p)
                rate = v["rate"]

                is_intra = (v["state"] == client.state_code)
                if is_intra:
                    half_rate = rate / 2.0
                    cgst_p = int(round(taxable_p * (half_rate / 100.0)))
                    sgst_p = cgst_p
                    igst_p = 0
                else:
                    cgst_p = 0
                    sgst_p = 0
                    igst_p = int(round(taxable_p * (rate / 100.0)))

                total_p = taxable_p + cgst_p + sgst_p + igst_p

                # Line item
                line_items = [
                    {
                        "description": v["item"],
                        "hsn_sac": v["hsn"],
                        "qty": 1,
                        "rate_paise": taxable_p,
                        "taxable_paise": taxable_p,
                        "gst_rate": rate,
                        "cgst_paise": cgst_p,
                        "sgst_paise": sgst_p,
                        "igst_paise": igst_p,
                        "cess_paise": 0,
                    }
                ]

                # Status: First 20 are final (CA approved), remaining are draft
                entry_status = "final" if i < 20 else "draft"
                approver_id = partner_user.id if entry_status == "final" else None
                approved_time = inv_date + timedelta(days=3) if entry_status == "final" else None

                target_acc = client._accounts.get(v["acc"])
                account_id = target_acc.id if target_acc else None

                entry = Entry(
                    organization_id=org.id,
                    client_id=client.id,
                    financial_year_id=client._fy.id,
                    entry_type="purchase",
                    voucher_number=f"PUR-{invoice_counter}",
                    invoice_number=inv_num,
                    invoice_date=inv_date,
                    party_name=v["name"],
                    party_gstin=supplier_gstin,
                    place_of_supply=client.state_code,
                    taxable_value_paise=taxable_p,
                    cgst_paise=cgst_p,
                    sgst_paise=sgst_p,
                    igst_paise=igst_p,
                    cess_paise=0,
                    round_off_paise=0,
                    total_amount_paise=total_p,
                    line_items=line_items,
                    debit_account_id=account_id,
                    status=entry_status,
                    is_itc_eligible=True,
                    approved_by_user_id=approver_id,
                    approved_at=approved_time
                )
                db.add(entry)
                all_created_entries.append(entry)

        # 5. Insert Deliberate Exceptions across clients for CA Review Demo
        # Case A: Blocked Credit under Section 17(5) - Taj Caterers (Food & Buffet)
        cat_taxable = 3500000 # ₹35,000.00
        cat_tax = int(round(cat_taxable * 0.05)) # 5% GST
        cat_entry = Entry(
            organization_id=org.id,
            client_id=clients[0].id,
            financial_year_id=clients[0]._fy.id,
            entry_type="purchase",
            invoice_number="TAJ-BANQ-901",
            invoice_date=datetime(2024, 7, 18, tzinfo=timezone.utc),
            party_name="Taj Banquets & Catering Services",
            party_gstin=generate_valid_gstin("27", "AABCT", "7788"),
            place_of_supply="27",
            taxable_value_paise=cat_taxable,
            cgst_paise=cat_tax // 2,
            sgst_paise=cat_tax // 2,
            igst_paise=0,
            cess_paise=0,
            total_amount_paise=cat_taxable + cat_tax,
            line_items=[{"description": "Annual Corporate Executive Buffet & Catering", "hsn_sac": "9963", "gst_rate": 5.0, "taxable_paise": cat_taxable, "cgst_paise": cat_tax//2, "sgst_paise": cat_tax//2, "igst_paise": 0, "cess_paise": 0}],
            status="draft",
            is_itc_eligible=False,
            itc_blocked_reason="Section 17(5)(b)(i) - Food, beverages and outdoor catering",
            debit_account_id=clients[0]._accounts.get("4080").id
        )
        db.add(cat_entry)
        db.flush()

        exc_cat = ExceptionRecord(
            organization_id=org.id,
            client_id=clients[0].id,
            entry_id=cat_entry.id,
            severity="medium",
            exception_type="blocked_credit_17_5",
            title="Blocked ITC under Section 17(5)(b) — Catering Services",
            description="Voucher line item is for food & outdoor catering. Under Section 17(5)(b)(i), ITC is blocked unless used as an outward taxable supply.",
            evidence={"keyword": "Catering", "supplier": "Taj Banquets", "tax_paise": cat_tax},
            suggested_fix="Confirm if business exception applies or mark ITC as ineligible in Table 4(D) of GSTR-3B.",
            status="open"
        )
        db.add(exc_cat)

        # Case B: Tax Type Mismatch (IGST charged on Intra-state supply)
        tt_taxable = 5000000 # ₹50,000.00
        tt_tax = int(round(tt_taxable * 0.18))
        tt_entry = Entry(
            organization_id=org.id,
            client_id=clients[0].id, # Client in MH (27)
            financial_year_id=clients[0]._fy.id,
            entry_type="purchase",
            invoice_number="TECH-MUM-8841",
            invoice_date=datetime(2024, 7, 22, tzinfo=timezone.utc),
            party_name="Mumbai Software Solutions Private Limited",
            party_gstin=generate_valid_gstin("27", "AABCM", "9900"), # Supplier in MH (27)
            place_of_supply="27", # Intra-state!
            taxable_value_paise=tt_taxable,
            cgst_paise=0, # Wrongly booked as IGST!
            sgst_paise=0,
            igst_paise=tt_tax,
            cess_paise=0,
            total_amount_paise=tt_taxable + tt_tax,
            line_items=[{"description": "Custom ERP Module Development", "hsn_sac": "9983", "gst_rate": 18.0, "taxable_paise": tt_taxable, "cgst_paise": 0, "sgst_paise": 0, "igst_paise": tt_tax, "cess_paise": 0}],
            status="draft",
            is_itc_eligible=True,
            debit_account_id=clients[0]._accounts.get("4010").id
        )
        db.add(tt_entry)
        db.flush()

        exc_tt = ExceptionRecord(
            organization_id=org.id,
            client_id=clients[0].id,
            entry_id=tt_entry.id,
            severity="high",
            exception_type="tax_type_mismatch",
            title="IGST Charged on Intra-State Supply",
            description="Both Supplier State (27 - Maharashtra) and Place of Supply (27) are identical. CGST & SGST must be charged, but IGST was billed.",
            evidence={"supplier_state": "27", "pos": "27", "igst_charged_paise": tt_tax},
            suggested_fix="Reclassify ₹9,000 IGST into ₹4,500 CGST + ₹4,500 SGST.",
            status="open"
        )
        db.add(exc_tt)

        # Case C: Invalid GSTIN Checksum
        inv_gstin_taxable = 2000000
        inv_entry = Entry(
            organization_id=org.id,
            client_id=clients[1].id,
            financial_year_id=clients[1]._fy.id,
            entry_type="purchase",
            invoice_number="BLR-SUP-104",
            invoice_date=datetime(2024, 7, 25, tzinfo=timezone.utc),
            party_name="Karnataka Hardware & Networking Hub",
            party_gstin="29AABCZ9999K1Z9", # Invalid checksum digit
            place_of_supply="29",
            taxable_value_paise=inv_gstin_taxable,
            cgst_paise=180000,
            sgst_paise=180000,
            igst_paise=0,
            cess_paise=0,
            total_amount_paise=inv_gstin_taxable + 360000,
            line_items=[{"description": "Cat-6 Cables & Patch Panels", "hsn_sac": "8544", "gst_rate": 18.0, "taxable_paise": inv_gstin_taxable, "cgst_paise": 180000, "sgst_paise": 180000, "igst_paise": 0, "cess_paise": 0}],
            status="draft",
            is_itc_eligible=True,
            debit_account_id=clients[1]._accounts.get("4060").id
        )
        db.add(inv_entry)
        db.flush()

        exc_inv = ExceptionRecord(
            organization_id=org.id,
            client_id=clients[1].id,
            entry_id=inv_entry.id,
            severity="high",
            exception_type="gstin_invalid",
            title="Invalid Supplier GSTIN Checksum",
            description="Supplier GSTIN '29AABCZ9999K1Z9' failed statutory Mod-36 checksum calculation.",
            evidence={"gstin": "29AABCZ9999K1Z9"},
            suggested_fix="Review physical invoice to verify check digit.",
            status="open"
        )
        db.add(exc_inv)

        # Case D: Arithmetic Mismatch
        arith_entry = Entry(
            organization_id=org.id,
            client_id=clients[2].id,
            financial_year_id=clients[2]._fy.id,
            entry_type="purchase",
            invoice_number="DEL-PKG-771",
            invoice_date=datetime(2024, 7, 28, tzinfo=timezone.utc),
            party_name="Delhi Packaging Industries",
            party_gstin=generate_valid_gstin("07", "AABCD", "3322"),
            place_of_supply="07",
            taxable_value_paise=1000000, # ₹10,000
            cgst_paise=90000,           # ₹900
            sgst_paise=90000,           # ₹900
            igst_paise=0,
            cess_paise=0,
            round_off_paise=0,
            total_amount_paise=1250000, # Stated ₹12,500 instead of ₹11,800 (₹700 error)
            line_items=[{"description": "Corrugated Boxes", "hsn_sac": "4819", "gst_rate": 18.0, "taxable_paise": 1000000, "cgst_paise": 90000, "sgst_paise": 90000, "igst_paise": 0, "cess_paise": 0}],
            status="draft",
            is_itc_eligible=True,
            debit_account_id=clients[2]._accounts.get("4060").id
        )
        db.add(arith_entry)
        db.flush()

        exc_arith = ExceptionRecord(
            organization_id=org.id,
            client_id=clients[2].id,
            entry_id=arith_entry.id,
            severity="high",
            exception_type="arithmetic_error",
            title="Invoice Total Arithmetic Mismatch",
            description="Calculated total (Taxable ₹10,000 + Taxes ₹1,800 = ₹11,800) does not match stated invoice total ₹12,500. Discrepancy: ₹700.00.",
            evidence={"stated_total_paise": 1250000, "computed_total_paise": 1180000, "diff_paise": 70000},
            suggested_fix="Correct invoice total or verify extra charges with supplier.",
            status="open"
        )
        db.add(exc_arith)

        # 6. GSTR-2B Data for July 2024 with Deliberate Issues
        print("Seeding GSTR-2B records for July 2024 reconciliation...")
        # 1. Exact Match: Amazon Web Services
        aws_entry = next((e for e in all_created_entries if "Amazon" in e.party_name and e.client_id == clients[0].id), None)
        if aws_entry:
            rec_aws = GSTR2BRecord(
                organization_id=org.id,
                client_id=clients[0].id,
                return_period="072024",
                supplier_gstin=aws_entry.party_gstin,
                supplier_name=aws_entry.party_name,
                invoice_number=aws_entry.invoice_number,
                invoice_date=aws_entry.invoice_date,
                taxable_value_paise=aws_entry.taxable_value_paise,
                igst_paise=aws_entry.igst_paise,
                cgst_paise=aws_entry.cgst_paise,
                sgst_paise=aws_entry.sgst_paise,
                cess_paise=0,
                itc_availability="Y",
                reconciliation_status="matched",
                matched_entry_id=aws_entry.id,
                match_score=1.0
            )
            db.add(rec_aws)

        # 2. Amount Mismatch: Supplier uploaded wrong amount (₹18,000 tax vs Books ₹16,200)
        jio_entry = next((e for e in all_created_entries if "Reliance" in e.party_name and e.client_id == clients[0].id), None)
        if jio_entry:
            rec_jio = GSTR2BRecord(
                organization_id=org.id,
                client_id=clients[0].id,
                return_period="072024",
                supplier_gstin=jio_entry.party_gstin,
                supplier_name=jio_entry.party_name,
                invoice_number=jio_entry.invoice_number,
                invoice_date=jio_entry.invoice_date,
                taxable_value_paise=jio_entry.taxable_value_paise + 100000, # Discrepancy
                igst_paise=0,
                cgst_paise=jio_entry.cgst_paise + 9000,
                sgst_paise=jio_entry.sgst_paise + 9000,
                cess_paise=0,
                itc_availability="Y",
                reconciliation_status="partially_matched",
                matched_entry_id=jio_entry.id,
                match_score=0.85,
                match_discrepancies={"tax_mismatch": {"books_tax": jio_entry.cgst_paise + jio_entry.sgst_paise, "gstr2b_tax": jio_entry.cgst_paise + jio_entry.sgst_paise + 18000}}
            )
            db.add(rec_jio)

        # 3. In 2B Not in Books: Vendor uploaded invoice, but CA's client missed submitting bill
        rec_unclaimed = GSTR2BRecord(
            organization_id=org.id,
            client_id=clients[0].id,
            return_period="072024",
            supplier_gstin=generate_valid_gstin("27", "AABCB", "8821"),
            supplier_name="Blue Dart Express Courier Services",
            invoice_number="BD-MUM-992144",
            invoice_date=datetime(2024, 7, 12, tzinfo=timezone.utc),
            taxable_value_paise=850000, # ₹8,500.00
            igst_paise=0,
            cgst_paise=76500,
            sgst_paise=76500,
            cess_paise=0,
            itc_availability="Y",
            reconciliation_status="gstr2b_only"
        )
        db.add(rec_unclaimed)

        # 7. Bank Statements (1 per client)
        print("Seeding Bank statements for clients...")
        for c_idx, client in enumerate(clients):
            stmt = BankStatement(
                organization_id=org.id,
                client_id=client.id,
                bank_name="HDFC Bank" if c_idx == 0 else ("ICICI Bank" if c_idx == 1 else "State Bank of India"),
                account_number_masked=f"XXXXXXXX{9821 + c_idx}",
                statement_period="July 2024"
            )
            db.add(stmt)
            db.flush()

            # Seed 10 realistic lines
            running_balance = 50000000 # ₹5 Lakhs
            for line_idx in range(10):
                line_date = datetime(2024, 7, 2, tzinfo=timezone.utc) + timedelta(days=line_idx * 3)
                if line_idx % 2 == 0:
                    debit_p = random.randint(500000, 3000000)
                    credit_p = 0
                    running_balance -= debit_p
                    narration = f"NEFT / UTR{random.randint(100000, 999999)} / Vendor Payment"
                else:
                    debit_p = 0
                    credit_p = random.randint(1000000, 5000000)
                    running_balance += credit_p
                    narration = f"RTGS / CMS / Client Sales Inflow / REF{random.randint(100000, 999999)}"

                line = BankStatementLine(
                    statement_id=stmt.id,
                    txn_date=line_date,
                    value_date=line_date,
                    narration=narration,
                    reference_no=f"UTR{random.randint(1000000, 9999999)}",
                    debit_paise=debit_p,
                    credit_paise=credit_p,
                    balance_paise=running_balance,
                    reconciliation_status="matched" if line_idx < 6 else "unmatched",
                    match_reason="Matched on UTR & amount" if line_idx < 6 else None
                )
                db.add(line)

        # 8. Seed Learned Categorisation Rules
        rule1 = CategorisationRule(
            organization_id=org.id,
            client_id=clients[0].id,
            rule_type="vendor_exact",
            match_pattern="Amazon Web Services",
            target_account_id=clients[0]._accounts.get("4010").id,
            confidence=0.99,
            source="learned_ca_correction",
            usage_count=18,
            last_used_at=datetime.now(timezone.utc)
        )
        rule2 = CategorisationRule(
            organization_id=org.id,
            client_id=clients[0].id,
            rule_type="vendor_exact",
            match_pattern="Reliance Jio",
            target_account_id=clients[0]._accounts.get("4050").id,
            confidence=0.99,
            source="learned_ca_correction",
            usage_count=14,
            last_used_at=datetime.now(timezone.utc)
        )
        db.add_all([rule1, rule2])

        db.commit()
        print("Database seeding completed successfully!")
        print("Mehta & Associates CA Firm Demo:")
        print("  Partner Login: partner@mehta-ca.in / Partner@Accuro2025!")
        print("  Article Login: article@mehta-ca.in / Article@Accuro2025!")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
