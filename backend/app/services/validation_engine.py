import re
from datetime import datetime, timezone, date
from typing import List, Dict, Any, Optional, Tuple

# Indian GST State Codes Map
GST_STATE_CODES = {
    "01": "Jammu and Kashmir", "02": "Himachal Pradesh", "03": "Punjab", "04": "Chandigarh",
    "05": "Uttarakhand", "06": "Haryana", "07": "Delhi", "08": "Rajasthan",
    "09": "Uttar Pradesh", "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh",
    "13": "Nagaland", "14": "Manipur", "15": "Mizoram", "16": "Tripura",
    "17": "Meghalaya", "18": "Assam", "19": "West Bengal", "20": "Jharkhand",
    "21": "Odisha", "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat",
    "25": "Daman and Diu", "26": "Dadra and Nagar Haveli", "27": "Maharashtra",
    "28": "Andhra Pradesh (Old)", "29": "Karnataka", "30": "Goa", "31": "Lakshadweep",
    "32": "Kerala", "33": "Tamil Nadu", "34": "Puducherry", "35": "Andaman and Nicobar Islands",
    "36": "Telangana", "37": "Andhra Pradesh", "38": "Ladakh", "97": "Other Territory", "99": "Centre Jurisdiction"
}

VALID_GST_RATES = {0.0, 0.1, 0.25, 1.5, 3.0, 5.0, 12.0, 18.0, 28.0}

KNOWN_HSN_RATES = {
    "9983": [18.0], # IT & Consulting Services
    "9973": [18.0], # Software / IP Licensing
    "9965": [5.0, 18.0], # Goods Transport Agency (GTA)
    "9963": [5.0, 12.0, 18.0], # Accommodation / Restaurant
    "8471": [18.0], # Computers and processing machines
    "4901": [0.0],  # Printed books
    "9972": [18.0], # Real Estate Services
    "3004": [12.0], # Medicaments
    "8703": [28.0], # Motor cars and motor vehicles
    "9968": [18.0], # Postal and courier services
}

SECTION_17_5_KEYWORDS = [
    ("motor vehicle", "Section 17(5)(a) - Motor vehicles and conveyances for passenger transport"),
    ("car hire", "Section 17(5)(a) - Motor vehicle hire/lease"),
    ("vehicle repair", "Section 17(5)(ab) - Repair/servicing of motor vehicles"),
    ("food", "Section 17(5)(b)(i) - Food and beverages"),
    ("catering", "Section 17(5)(b)(i) - Outdoor catering"),
    ("beverage", "Section 17(5)(b)(i) - Beverages and refreshment"),
    ("restaurant", "Section 17(5)(b)(i) - Food and restaurant services"),
    ("buffet", "Section 17(5)(b)(i) - Food and catering services"),
    ("club", "Section 17(5)(b)(ii) - Membership of a club"),
    ("gym", "Section 17(5)(b)(ii) - Health and fitness centre membership"),
    ("beauty", "Section 17(5)(b)(i) - Beauty treatment / cosmetic"),
    ("travel benefit", "Section 17(5)(b)(iii) - Travel benefits extended to employees on leave"),
    ("gift", "Section 17(5)(h) - Goods lost, stolen, destroyed, written off or gifted"),
    ("personal", "Section 17(5)(g) - Goods or services used for personal consumption"),
    ("works contract", "Section 17(5)(c) - Works contract services for construction of immovable property"),
]

class ValidationIssue:
    def __init__(self, severity: str, exception_type: str, title: str, description: str, evidence: dict, suggested_fix: str = None):
        self.severity = severity # "high", "medium", "low"
        self.exception_type = exception_type
        self.title = title
        self.description = description
        self.evidence = evidence
        self.suggested_fix = suggested_fix

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "exception_type": self.exception_type,
            "title": self.title,
            "description": self.description,
            "evidence": self.evidence,
            "suggested_fix": self.suggested_fix,
        }

def validate_gstin_checksum(gstin: str) -> bool:
    """
    Validate 15-character Indian GSTIN format and Luhn mod 36 checksum digit.
    Format: 2 digits (State) + 5 chars (PAN alpha) + 4 digits (PAN num) + 1 char (PAN alpha)
            + 1 char (Entity number 1-9/A-Z) + 'Z' (default 14th char) + 1 char (Checksum)
    """
    if not gstin or len(gstin) != 15:
        return False
    
    gstin = gstin.upper().strip()
    pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
    if not re.match(pattern, gstin):
        return False

    # Verify state code is valid
    state_code = gstin[:2]
    if state_code not in GST_STATE_CODES:
        return False

    # Luhn Mod 36 Algorithm Checksum
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    char_to_val = {c: i for i, c in enumerate(chars)}
    
    total = 0
    for i in range(14):
        c = gstin[i]
        val = char_to_val.get(c, 0)
        # Weight multiplier: alternating 1 and 2
        weight = 1 if (i % 2 == 0) else 2
        factor = val * weight
        quotient = factor // 36
        remainder = factor % 36
        total += quotient + remainder

    check_val = (36 - (total % 36)) % 36
    expected_check_char = chars[check_val]
    
    return gstin[14] == expected_check_char

def calculate_gstin_checksum_char(gstin_first_14: str) -> str:
    """Helper to compute correct check digit for testing and synthetic generation."""
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    char_to_val = {c: i for i, c in enumerate(chars)}
    total = 0
    for i in range(14):
        c = gstin_first_14[i]
        val = char_to_val.get(c, 0)
        weight = 1 if (i % 2 == 0) else 2
        factor = val * weight
        quotient = factor // 36
        remainder = factor % 36
        total += quotient + remainder
    check_val = (36 - (total % 36)) % 36
    return chars[check_val]

class ValidationEngine:
    """
    Deterministic rule-based tax, compliance, and arithmetic verification engine.
    Never relies on LLMs for validation logic.
    """

    @staticmethod
    def validate_entry(
        entry_data: dict,
        client_state_code: str,
        fy_start_date: datetime,
        fy_end_date: datetime,
        existing_entries: List[dict] = None,
        vendor_history: List[dict] = None
    ) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []

        # 1. Missing Mandatory Fields
        mandatory_fields = [
            ("invoice_number", "Invoice Number"),
            ("invoice_date", "Invoice Date"),
            ("party_name", "Supplier / Customer Name"),
            ("taxable_value_paise", "Taxable Value"),
            ("total_amount_paise", "Total Amount"),
        ]
        for field_key, field_name in mandatory_fields:
            val = entry_data.get(field_key)
            if val is None or (isinstance(val, str) and not val.strip()):
                issues.append(ValidationIssue(
                    severity="high",
                    exception_type="missing_mandatory_field",
                    title=f"Missing {field_name}",
                    description=f"The invoice is missing the mandatory tax field: {field_name}.",
                    evidence={"field": field_key, "value": val},
                    suggested_fix=f"Extract or manually enter {field_name} from the source document."
                ))

        # 2. GSTIN Format and Luhn Mod-36 Checksum Validation
        supplier_gstin = (entry_data.get("party_gstin") or "").strip().upper()
        if supplier_gstin:
            if not validate_gstin_checksum(supplier_gstin):
                issues.append(ValidationIssue(
                    severity="high",
                    exception_type="gstin_invalid",
                    title="Invalid Supplier GSTIN",
                    description=f"The supplier GSTIN '{supplier_gstin}' failed statutory format or Mod-36 checksum verification.",
                    evidence={"gstin": supplier_gstin, "length": len(supplier_gstin)},
                    suggested_fix="Check the source invoice document to verify character OCR (e.g., '0' vs 'O', '1' vs 'I')."
                ))

        # 3. Tax Logic: IGST vs CGST+SGST (Inter-state vs Intra-state)
        place_of_supply = (entry_data.get("place_of_supply") or "").strip()
        supplier_state = supplier_gstin[:2] if len(supplier_gstin) >= 2 else client_state_code

        cgst_p = entry_data.get("cgst_paise", 0) or 0
        sgst_p = entry_data.get("sgst_paise", 0) or 0
        igst_p = entry_data.get("igst_paise", 0) or 0

        if place_of_supply and supplier_state:
            is_intra_state = (supplier_state == place_of_supply)
            if is_intra_state:
                # Intra-state: Must have CGST + SGST, no IGST
                if igst_p > 0:
                    issues.append(ValidationIssue(
                        severity="high",
                        exception_type="tax_type_mismatch",
                        title="IGST Charged on Intra-State Supply",
                        description=(
                            f"Supplier state ({supplier_state} - {GST_STATE_CODES.get(supplier_state, 'Unknown')}) "
                            f"matches Place of Supply ({place_of_supply}). Supply is intra-state, "
                            f"so CGST and SGST must apply instead of IGST."
                        ),
                        evidence={"supplier_state": supplier_state, "pos": place_of_supply, "igst_paise": igst_p},
                        suggested_fix="Reclassify IGST into equal halves of CGST and SGST."
                    ))
                if cgst_p != sgst_p:
                    issues.append(ValidationIssue(
                        severity="medium",
                        exception_type="tax_type_mismatch",
                        title="CGST and SGST Imbalance",
                        description=f"CGST (₹{cgst_p/100:.2f}) and SGST (₹{sgst_p/100:.2f}) must be exactly equal on intra-state supplies.",
                        evidence={"cgst_paise": cgst_p, "sgst_paise": sgst_p},
                        suggested_fix="Adjust CGST and SGST to match equal 50:50 statutory split."
                    ))
            else:
                # Inter-state: Must have IGST, no CGST/SGST
                if cgst_p > 0 or sgst_p > 0:
                    issues.append(ValidationIssue(
                        severity="high",
                        exception_type="tax_type_mismatch",
                        title="CGST/SGST Charged on Inter-State Supply",
                        description=(
                            f"Supplier state ({supplier_state} - {GST_STATE_CODES.get(supplier_state, 'Unknown')}) "
                            f"differs from Place of Supply ({place_of_supply}). Supply is inter-state, "
                            f"so IGST must apply instead of CGST/SGST."
                        ),
                        evidence={"supplier_state": supplier_state, "pos": place_of_supply, "cgst_paise": cgst_p, "sgst_paise": sgst_p},
                        suggested_fix="Reclassify CGST and SGST total into IGST."
                    ))

        # 4. Arithmetic Checks
        taxable_p = entry_data.get("taxable_value_paise", 0) or 0
        cess_p = entry_data.get("cess_paise", 0) or 0
        round_off_p = entry_data.get("round_off_paise", 0) or 0
        total_p = entry_data.get("total_amount_paise", 0) or 0

        computed_total = taxable_p + cgst_p + sgst_p + igst_p + cess_p + round_off_p
        diff_total = abs(computed_total - total_p)
        if diff_total > 100: # Tolerance of ₹1.00 (100 paise) for fractional rounding
            issues.append(ValidationIssue(
                severity="high",
                exception_type="arithmetic_error",
                title="Invoice Arithmetic Mismatch",
                description=(
                    f"Computed total (Taxable ₹{taxable_p/100:.2f} + Taxes ₹{(cgst_p+sgst_p+igst_p+cess_p)/100:.2f} "
                    f"+ Round-off ₹{round_off_p/100:.2f} = ₹{computed_total/100:.2f}) does not match invoice total ₹{total_p/100:.2f}. "
                    f"Discrepancy: ₹{diff_total/100:.2f}."
                ),
                evidence={"taxable_paise": taxable_p, "taxes_paise": cgst_p+sgst_p+igst_p+cess_p, "stated_total": total_p, "computed_total": computed_total},
                suggested_fix="Review line item arithmetic and round-off adjustments."
            ))

        # Check line items sum to taxable value if line items are provided
        line_items = entry_data.get("line_items") or []
        if line_items:
            sum_line_taxable = sum((item.get("taxable_paise") or 0) for item in line_items)
            if abs(sum_line_taxable - taxable_p) > 100:
                issues.append(ValidationIssue(
                    severity="medium",
                    exception_type="arithmetic_error",
                    title="Line Items Sum Mismatch",
                    description=f"Sum of line items taxable value (₹{sum_line_taxable/100:.2f}) differs from header taxable value (₹{taxable_p/100:.2f}).",
                    evidence={"lines_sum_paise": sum_line_taxable, "header_taxable_paise": taxable_p},
                    suggested_fix="Reconcile itemized lines with invoice summary."
                ))

            # GST rate slabs & HSN sanity check
            for idx, item in enumerate(line_items):
                rate = float(item.get("gst_rate") or 0.0)
                if rate not in VALID_GST_RATES:
                    issues.append(ValidationIssue(
                        severity="medium",
                        exception_type="hsn_rate_mismatch",
                        title=f"Non-Standard GST Rate in Line {idx+1}",
                        description=f"GST rate {rate}% is not among standard statutory GST slabs (0%, 0.1%, 0.25%, 1.5%, 3%, 5%, 12%, 18%, 28%).",
                        evidence={"line_index": idx, "rate": rate, "item": item.get("description")},
                        suggested_fix="Confirm rate slab with supplier invoice schedule."
                    ))

                hsn = str(item.get("hsn_sac") or "").strip()[:4]
                if hsn in KNOWN_HSN_RATES and rate not in KNOWN_HSN_RATES[hsn]:
                    expected_rates = ", ".join(f"{r}%" for r in KNOWN_HSN_RATES[hsn])
                    issues.append(ValidationIssue(
                        severity="medium",
                        exception_type="hsn_rate_mismatch",
                        title=f"HSN {hsn} Rate Anomaly in Line {idx+1}",
                        description=f"HSN/SAC {hsn} typically attracts {expected_rates}, but {rate}% was charged on '{item.get('description')}'.",
                        evidence={"hsn": hsn, "applied_rate": rate, "standard_rates": KNOWN_HSN_RATES[hsn]},
                        suggested_fix=f"Verify if specific exemption or composition rate applies."
                    ))

        # 5. Date Checks & Section 16(4) ITC Claim Deadline
        inv_date = entry_data.get("invoice_date")
        if isinstance(inv_date, str):
            try:
                inv_date = datetime.fromisoformat(inv_date.replace("Z", "+00:00"))
            except Exception:
                inv_date = None

        if inv_date:
            now = datetime.now(timezone.utc)
            # Future Date Check
            if inv_date > now:
                issues.append(ValidationIssue(
                    severity="high",
                    exception_type="arithmetic_error",
                    title="Future Invoice Date",
                    description=f"The invoice date {inv_date.strftime('%d-%b-%Y')} is in the future.",
                    evidence={"invoice_date": inv_date.isoformat(), "current_date": now.isoformat()},
                    suggested_fix="Correct invoice date from physical voucher."
                ))

            # FY Boundary Check
            if fy_start_date and fy_end_date:
                # normalize tz
                inv_date_utc = inv_date if inv_date.tzinfo else inv_date.replace(tzinfo=timezone.utc)
                fy_start_utc = fy_start_date if fy_start_date.tzinfo else fy_start_date.replace(tzinfo=timezone.utc)
                fy_end_utc = fy_end_date if fy_end_date.tzinfo else fy_end_date.replace(tzinfo=timezone.utc)

                if inv_date_utc < fy_start_utc or inv_date_utc > fy_end_utc:
                    issues.append(ValidationIssue(
                        severity="medium",
                        exception_type="arithmetic_error",
                        title="Invoice Outside Financial Year",
                        description=f"Invoice date {inv_date_utc.strftime('%d-%b-%Y')} falls outside active FY ({fy_start_utc.strftime('%d-%b-%Y')} to {fy_end_utc.strftime('%d-%b-%Y')}).",
                        evidence={"invoice_date": inv_date_utc.isoformat(), "fy_start": fy_start_utc.isoformat(), "fy_end": fy_end_utc.isoformat()},
                        suggested_fix="Verify if voucher belongs to prior period or next FY."
                    ))

            # Section 16(4) Time-Bar: 30th November following FY end
            if fy_end_date:
                next_nov_30 = datetime(fy_end_date.year, 11, 30, 23, 59, 59, tzinfo=timezone.utc)
                if now > next_nov_30:
                    issues.append(ValidationIssue(
                        severity="high",
                        exception_type="time_barred_16_4",
                        title="ITC Time-Barred under Section 16(4)",
                        description=(
                            f"Under Section 16(4) of the CGST Act, Input Tax Credit for FY {fy_end_date.year-1}-{str(fy_end_date.year)[-2:]} "
                            f"cannot be availed after 30th November {fy_end_date.year}. This credit is time-barred."
                        ),
                        evidence={"deadline": next_nov_30.isoformat(), "invoice_date": inv_date.isoformat()},
                        suggested_fix="Mark ITC as ineligible under Section 16(4) and book tax as expense."
                    ))

        # 6. Section 17(5) Blocked Credit Detection
        # Check narration, party name, and line item descriptions against statutory blocked categories
        party_name = (entry_data.get("party_name") or "").lower()
        all_descriptions = [party_name]
        for itm in line_items:
            all_descriptions.append((itm.get("description") or "").lower())

        combined_desc = " ".join(all_descriptions)
        for keyword, legal_ref in SECTION_17_5_KEYWORDS:
            if keyword in combined_desc:
                issues.append(ValidationIssue(
                    severity="medium",
                    exception_type="blocked_credit_17_5",
                    title="Potential Blocked ITC under Section 17(5)",
                    description=(
                        f"Line contains '{keyword}', indicating goods/services categorized as blocked credit "
                        f"under {legal_ref}. Review if this qualifies for business exceptions."
                    ),
                    evidence={"keyword_found": keyword, "legal_provision": legal_ref},
                    suggested_fix="Confirm with client if used for eligible outward supply, or mark as Ineligible ITC."
                ))
                break # Flag once per entry

        # 7. Duplicate Invoice Detection
        inv_num = (entry_data.get("invoice_number") or "").strip().upper()
        if existing_entries and inv_num:
            for past in existing_entries:
                past_inv = (past.get("invoice_number") or "").strip().upper()
                past_gstin = (past.get("party_gstin") or "").strip().upper()
                past_amount = past.get("total_amount_paise") or 0
                
                # Exact Duplicate
                if past_inv == inv_num and past_gstin == supplier_gstin and past.get("id") != entry_data.get("id"):
                    issues.append(ValidationIssue(
                        severity="high",
                        exception_type="duplicate_invoice",
                        title="Exact Duplicate Invoice Detected",
                        description=f"Invoice #{inv_num} from supplier {entry_data.get('party_name')} already exists in the system.",
                        evidence={"duplicate_entry_id": past.get("id"), "invoice_number": inv_num, "supplier_gstin": supplier_gstin},
                        suggested_fix="Verify if this document was re-uploaded or represents an amended bill."
                    ))
                    break

                # Fuzzy Duplicate: Same party + same amount + close date
                if past_gstin == supplier_gstin and past_amount == total_p and past.get("id") != entry_data.get("id"):
                    past_date = past.get("invoice_date")
                    if isinstance(past_date, str) and inv_date:
                        try:
                            p_date = datetime.fromisoformat(past_date.replace("Z", "+00:00"))
                            if abs((p_date - inv_date).days) <= 2 and past_inv != inv_num:
                                issues.append(ValidationIssue(
                                    severity="medium",
                                    exception_type="duplicate_invoice",
                                    title="Potential Fuzzy Duplicate",
                                    description=f"Another invoice from {entry_data.get('party_name')} with identical total ₹{total_p/100:.2f} exists on {p_date.strftime('%d-%b-%Y')} (#{past_inv}).",
                                    evidence={"related_entry_id": past.get("id"), "existing_invoice": past_inv, "amount_paise": total_p},
                                    suggested_fix="Check if same bill was uploaded under different invoice reference."
                                ))
                        except Exception:
                            pass

        # 8. Unusual Amount vs Vendor History
        if vendor_history and len(vendor_history) >= 2:
            amounts = [h.get("total_amount_paise", 0) for h in vendor_history if h.get("total_amount_paise")]
            if amounts:
                avg_amount = sum(amounts) / len(amounts)
                if total_p > 3 * avg_amount and total_p > 10000000: # Over 3x average and > ₹1 Lakh
                    issues.append(ValidationIssue(
                        severity="medium",
                        exception_type="unusual_amount",
                        title="Unusual Invoice Amount for Vendor",
                        description=f"Total amount ₹{total_p/100:,.2f} is more than 3x the historical average (₹{avg_amount/100:,.2f}) for this vendor.",
                        evidence={"current_amount_paise": total_p, "historical_average_paise": int(avg_amount), "sample_size": len(amounts)},
                        suggested_fix="Verify whether a bulk order, annual contract, or decimal placement error occurred."
                    ))

        return issues
