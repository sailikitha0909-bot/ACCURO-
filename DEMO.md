# Accuro — 5-Minute Demonstration Walkthrough

> **"Accurate accounts. You review, Accuro does the rest."**

This guided walkthrough demonstrates how **Accuro** automates the first pass of accounting work for an Indian CA firm, allowing the CA to focus strictly on compliance exceptions, approve vouchers, and export clean data directly into Tally Prime.

---

## Prerequisites
Ensure the application is running:
- **Web App**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Step 1: Sign in with Pre-Seeded CA Accounts (0:00 - 0:30)
1. Open [http://localhost:3000/login](http://localhost:3000/login).
2. Notice the clean, trustworthy finance interface with deep blue (`#1E3A8A`) branding.
3. Under **1-Click Demo Accounts**, click **CA Partner** (`partner@mehta-ca.in`).
4. You are taken immediately to the **Executive Dashboard**.
   - Note the real-time operational cards computed from the database: Documents Processed, Auto-cleared Rate, Priority Exceptions Open, and Estimated Hours Saved.
   - Strictly zero fake or hardcoded metrics.

---

## Step 2: Ingest Invoices via Document Pipeline (0:30 - 1:30)
1. Navigate to **Documents** in the sidebar.
2. Select client **Apex Retailers Private Limited**.
3. Drag and drop a sample invoice (or select any PDF/image/statement).
4. Watch the document intake pipeline execute:
   - **SHA-256 Hash**: The system computes a hash to detect duplicate re-uploads immutably.
   - **Extraction**: Fields (Supplier Name, GSTIN, Invoice #, Date, Line Items, HSN, Taxable Value, CGST, SGST, IGST, Cess, Total) are extracted alongside visual bounding boxes and confidence scores.
   - **Deterministic Validation**: The invoice is checked for Luhn Mod-36 GSTIN check digit, intra vs inter-state tax slabs, arithmetic, Section 16(4) time-bars, and Section 17(5) blocked credit.
   - **Continuous Categorisation**: Chart of accounts ledger is resolved in order: Learned CA Rules $\rightarrow$ Vendor Rules $\rightarrow$ HSN code.

---

## Step 3: Inspect the Priority Exception Queue (1:30 - 2:30)
1. Navigate to **Exceptions** in the sidebar (or click the alert card on the Dashboard).
2. Review the prioritised list sorted by statutory severity:
   - **Critical (High)**: `IGST Charged on Intra-State Supply` on Mumbai Software Solutions (Supplier State 27 matches POS 27).
   - **Critical (High)**: `Invalid Supplier GSTIN Checksum` on Karnataka Hardware (failed Luhn Mod-36 check digit).
   - **Critical (High)**: `Invoice Total Arithmetic Mismatch` on Delhi Packaging (stated ₹12,500 vs computed ₹11,800).
   - **Warning (Medium)**: `Blocked ITC under Section 17(5)(b)` on Taj Banquets (food and catering services).
3. Click an exception to view the statutory tax analysis, deterministic evidence JSON, and the recommended CA fix.

---

## Step 4: Split-Pane Interactive Document Review (2:30 - 3:30)
1. In the exception detail pane, click **Open Split-Pane Document Viewer** (or open any document from `/documents`).
2. Notice the dense 50/50 split layout:
   - **Left Pane**: Original document viewer showing the physical tax voucher layout with interactive bounding boxes.
   - **Right Pane**: Editable schema with confidence scores and ledger selection.
3. Click on the **Supplier Name** or **GSTIN** bounding box on the document canvas; observe the corresponding field focus on the right.
4. On the right, reassign the ledger account (e.g. from *Office Expenses* to *Software & SaaS Subscriptions*).
5. Click **Save Draft**: Accuro immediately records a **Learned Categorisation Rule** for this supplier. Next month's invoice will auto-categorize to this ledger!

---

## Step 5: Multi-Way GSTR-2B & Bank Reconciliation (3:30 - 4:15)
1. Navigate to **GST Reconciliation** in the sidebar.
2. Inspect the **GSTR-2B vs Books (July 2024)** schedule:
   - **Eligible Claimable ITC**: Matched vouchers where supplier filed GSTR-1 and ITC is available.
   - **ITC at Immediate Risk**: Invoices recorded in books where the supplier has not filed GSTR-1.
   - **Blocked Credit (Section 17(5))**: Statutorily ineligible items separated for Table 4(D) reporting.
3. Scroll down to the **Vendor Follow-up Schedule**:
   - See defaulting suppliers (e.g. *Late Vendor Pvt Ltd*).
   - Click **Draft Reminder** to copy an auto-drafted WhatsApp or Email follow-up notice with 1 click.
4. Switch to the **Bank Statement Reconciliation** tab to view auto-matched transactions against UTR numbers and settlement amounts.

---

## Step 6: CA Partner Approval Gate (4:15 - 4:45)
1. As **CA Partner**, you hold sole approval authority.
2. On any draft entry or in the **Exceptions Queue**, click **Approve Voucher (CA)**.
3. The voucher status transitions from `draft` to `final`:
   - Approver ID (`CA Rajesh Mehta`) and approval timestamp are recorded.
   - Any open exceptions for this voucher are automatically marked `resolved`.
   - An immutable audit trail entry is created.
4. *(Optional verification)*: Sign in as **Article Staff** (`article@mehta-ca.in` / `Article@Accuro2025!`); observe that approval buttons are disabled and marked *"CA Approval Required"*.

---

## Step 7: Export to Tally Prime XML (4:45 - 5:00)
1. Navigate to **Reports & Exports** in the sidebar.
2. Select client **Apex Retailers Private Limited**.
3. View the balanced **Trial Balance** and **GSTR-3B Liability Schedule**.
4. In the top right actions, click **Export Tally XML (Vouchers)**.
5. Accuro downloads a standard Tally Prime XML file (`Accuro_TallyPrime_Import.xml`):
   - Fully structured `<ENVELOPE>` voucher schema.
   - Contains party ledger (credit), expense ledger (debit), and CGST/SGST/IGST tax ledgers.
   - Carry the audit narration: *`AI-prepared draft by Accuro. Requires CA review.`*
6. In **Tally Prime**, go to *Import Data $\rightarrow$ Vouchers* and select the file—all accounting entries import directly into the company!

---

### End of Walkthrough
*Accuro: Accurate accounts. You review, Accuro does the rest.*
