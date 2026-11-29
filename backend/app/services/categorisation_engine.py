from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models import ChartOfAccount, CategorisationRule, Client

DEFAULT_INDIAN_CHART_OF_ACCOUNTS = [
    # Assets
    {"code": "1010", "name": "HDFC Bank Current Account", "type": "asset", "parent": "Bank Accounts"},
    {"code": "1020", "name": "ICICI Bank Current Account", "type": "asset", "parent": "Bank Accounts"},
    {"code": "1030", "name": "Cash-in-Hand", "type": "asset", "parent": "Cash-in-Hand"},
    {"code": "1110", "name": "Sundry Debtors (Trade Receivables)", "type": "asset", "parent": "Current Assets"},
    {"code": "1210", "name": "Computer & IT Equipment", "type": "asset", "parent": "Fixed Assets"},
    {"code": "1220", "name": "Office Furniture & Fixtures", "type": "asset", "parent": "Fixed Assets"},
    
    # Liabilities & GST Duties
    {"code": "2010", "name": "Sundry Creditors (Trade Payables)", "type": "liability", "parent": "Sundry Creditors"},
    {"code": "2110", "name": "CGST Input Tax Credit", "type": "liability", "parent": "Duties & Taxes"},
    {"code": "2120", "name": "SGST Input Tax Credit", "type": "liability", "parent": "Duties & Taxes"},
    {"code": "2130", "name": "IGST Input Tax Credit", "type": "liability", "parent": "Duties & Taxes"},
    {"code": "2140", "name": "TDS Payable (Section 194C/194J)", "type": "liability", "parent": "Duties & Taxes"},

    # Revenue
    {"code": "3010", "name": "Software Development & SaaS Revenue", "type": "revenue", "parent": "Direct Income"},
    {"code": "3020", "name": "Professional & Advisory Fees", "type": "revenue", "parent": "Direct Income"},
    {"code": "3030", "name": "Sale of Goods & Commodities", "type": "revenue", "parent": "Sales"},

    # Indirect Expenses
    {"code": "4010", "name": "Software & SaaS Subscriptions", "type": "expense", "parent": "Indirect Expenses"},
    {"code": "4020", "name": "Legal & Professional Charges", "type": "expense", "parent": "Indirect Expenses"},
    {"code": "4030", "name": "Office Rent & Facility Charges", "type": "expense", "parent": "Indirect Expenses"},
    {"code": "4040", "name": "Electricity & Utility Expenses", "type": "expense", "parent": "Indirect Expenses"},
    {"code": "4050", "name": "Telephone, Internet & Mobile", "type": "expense", "parent": "Indirect Expenses"},
    {"code": "4060", "name": "Printing, Stationery & Consumables", "type": "expense", "parent": "Indirect Expenses"},
    {"code": "4070", "name": "Travel & Conveyance", "type": "expense", "parent": "Indirect Expenses"},
    {"code": "4080", "name": "Staff Welfare & Catering (Section 17(5) Ineligible)", "type": "expense", "parent": "Indirect Expenses"},
    {"code": "4090", "name": "Courier & Freight Expenses", "type": "expense", "parent": "Indirect Expenses"},
    {"code": "4100", "name": "Bank Charges & Commission", "type": "expense", "parent": "Indirect Expenses"},
    {"code": "4110", "name": "Motor Vehicle Running & Maintenance", "type": "expense", "parent": "Indirect Expenses"},
]

DEFAULT_VENDOR_MAPPINGS = [
    ("amazon web services", "4010", 0.95),
    ("aws", "4010", 0.95),
    ("google cloud", "4010", 0.95),
    ("microsoft", "4010", 0.95),
    ("zoho", "4010", 0.95),
    ("reliance jio", "4050", 0.95),
    ("bharti airtel", "4050", 0.95),
    ("tata communications", "4050", 0.95),
    ("taj banquets", "4080", 0.95),
    ("catering", "4080", 0.90),
    ("restaurant", "4080", 0.90),
    ("stationery", "4060", 0.90),
    ("logistics", "4090", 0.90),
    ("freight", "4090", 0.90),
]

def seed_client_chart_of_accounts(db: Session, client: Client):
    """Seed initial chart of accounts for a new client."""
    accounts = []
    for item in DEFAULT_INDIAN_CHART_OF_ACCOUNTS:
        acc = ChartOfAccount(
            client_id=client.id,
            account_code=item["code"],
            account_name=item["name"],
            account_type=item["type"],
            parent_group=item["parent"],
            is_system_default=True
        )
        db.add(acc)
        accounts.append(acc)
    db.commit()
    return accounts

class CategorisationEngine:
    """
    Three-tier categorisation resolver:
    1. Learned CA corrections for this client
    2. Vendor / Pattern based rules
    3. LLM / HSN code suggestions
    """

    @staticmethod
    def resolve_category(
        db: Session,
        client_id: str,
        party_name: str,
        line_items: List[dict] = None,
        hsn_code: str = None
    ) -> Tuple[Optional[str], float, str]:
        """
        Returns: (account_id, confidence, rule_source)
        """
        p_name = (party_name or "").strip().lower()

        # Step 1: Check Learned CA Corrections for this client
        learned_rules = db.query(CategorisationRule).filter(
            CategorisationRule.client_id == client_id,
            CategorisationRule.source == "learned_ca_correction"
        ).order_by(CategorisationRule.usage_count.desc()).all()

        for rule in learned_rules:
            pattern = rule.match_pattern.strip().lower()
            if pattern and (pattern == p_name or pattern in p_name):
                # Update usage stats
                rule.usage_count += 1
                rule.last_used_at = datetime.now(timezone.utc)
                db.commit()
                return rule.target_account_id, 0.99, "learned_ca_correction"

        # Step 2: Check manual and default rules for this client
        client_rules = db.query(CategorisationRule).filter(
            CategorisationRule.client_id == client_id,
            CategorisationRule.source != "learned_ca_correction"
        ).all()

        for rule in client_rules:
            pattern = rule.match_pattern.strip().lower()
            if pattern and pattern in p_name:
                rule.usage_count += 1
                rule.last_used_at = datetime.now(timezone.utc)
                db.commit()
                return rule.target_account_id, rule.confidence or 0.90, "vendor_rule"

        # Step 3: Default vendor heuristics matched to Chart of Accounts
        for keyword, acc_code, conf in DEFAULT_VENDOR_MAPPINGS:
            if keyword in p_name:
                acc = db.query(ChartOfAccount).filter(
                    ChartOfAccount.client_id == client_id,
                    ChartOfAccount.account_code == acc_code
                ).first()
                if acc:
                    return acc.id, conf, "system_heuristic"

        # Step 4: HSN/SAC code heuristics
        if hsn_code:
            hsn_prefix = str(hsn_code).strip()[:4]
            if hsn_prefix in ("9983", "9973"): # IT / Software
                acc = db.query(ChartOfAccount).filter(
                    ChartOfAccount.client_id == client_id,
                    ChartOfAccount.account_code == "4010"
                ).first()
                if acc:
                    return acc.id, 0.85, "hsn_mapping"
            elif hsn_prefix == "9963": # Accommodation & Food
                acc = db.query(ChartOfAccount).filter(
                    ChartOfAccount.client_id == client_id,
                    ChartOfAccount.account_code == "4080"
                ).first()
                if acc:
                    return acc.id, 0.85, "hsn_mapping"

        # Fallback to general Office Expenses or first expense ledger
        fallback_acc = db.query(ChartOfAccount).filter(
            ChartOfAccount.client_id == client_id,
            ChartOfAccount.account_type == "expense"
        ).first()

        if fallback_acc:
            return fallback_acc.id, 0.50, "default_fallback"

        return None, 0.0, "none"

    @staticmethod
    def learn_ca_correction(
        db: Session,
        organization_id: str,
        client_id: str,
        party_name: str,
        target_account_id: str
    ):
        """
        Record a CA's manual correction as a learned rule so future invoices from this vendor
        are automatically categorized to the corrected ledger.
        """
        if not party_name or not target_account_id:
            return

        cleaned_pattern = party_name.strip()
        existing_rule = db.query(CategorisationRule).filter(
            CategorisationRule.client_id == client_id,
            CategorisationRule.match_pattern.ilike(cleaned_pattern)
        ).first()

        if existing_rule:
            existing_rule.target_account_id = target_account_id
            existing_rule.source = "learned_ca_correction"
            existing_rule.confidence = 0.99
            existing_rule.usage_count += 1
            existing_rule.last_used_at = datetime.now(timezone.utc)
        else:
            new_rule = CategorisationRule(
                organization_id=organization_id,
                client_id=client_id,
                rule_type="vendor_exact",
                match_pattern=cleaned_pattern,
                target_account_id=target_account_id,
                confidence=0.99,
                source="learned_ca_correction",
                usage_count=1,
                last_used_at=datetime.now(timezone.utc)
            )
            db.add(new_rule)
        db.commit()
