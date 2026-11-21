# Accuro

> **"Accurate accounts. You review, Accuro does the rest."**

Accuro (derived from *"accuracy"*) is a production-grade, multi-tenant web application engineered specifically for Indian Chartered Accountant (CA) firms. It automates the high-volume first pass of accounting work—document intake, double-entry voucher drafting, GST reconciliation, and compliance exception detection—so the CA only reviews exceptions.

> **Important Compliance Principle**: The CA always approves; the system never files returns or signs reports on its own. Every AI-generated draft carries the statutory notice:  
> *`AI-prepared draft by Accuro. Requires CA review.`*

---

## Architecture Overview

```
                                  +------------------------------------------+
                                  |            Accuro Web Client             |
                                  |  Next.js 14 + Tailwind + TanStack Table  |
                                  +------------------------------------------+
                                                       |  (REST / JWT)
                                                       v
+----------------------------------------------------------------------------------------------------------+
|                                           FastAPI Backend Service                                        |
|                                                                                                          |
|   +-----------------------+   +---------------------------+   +--------------------------------------+   |
|   | Document Ingestion    |   | Deterministic Validation  |   | Continuous Learning Engine           |   |
|   | - SHA-256 Deduplicate |   | - Luhn Mod-36 GSTIN Check |   | - Order 1: Learned CA Corrections    |   |
|   | - Multimodal Extract  |   | - Inter vs Intra Tax Slabs|   | - Order 2: Vendor Rules              |   |
|   | - Bounding Box Map    |   | - Section 16(4) Time Bar  |   | - Order 3: HSN / LLM Fallback        |   |
|   +-----------------------+   | - Section 17(5) Blocked   |   +--------------------------------------+   |
|                               +---------------------------+                                              |
|                                                                                                          |
|   +-------------------------------------------------------+   +--------------------------------------+   |
|   | Multi-Way Reconciliation Engine                       |   | Export & Compliance Engine           |   |
|   | - GSTR-2B Parser (JSON / Excel)                       |   | - Tally Prime XML (Vouchers)         |   |
|   | - Exact, Tolerant & Fuzzy Invoice Matching            |   | - Formatted Excel (.xlsx) & PDF      |   |
|   | - Bank Statement UTR / Amount Reconciliation          |   | - India DPDP Act Field Encryption    |   |
|   +-------------------------------------------------------+   +--------------------------------------+   |
+----------------------------------------------------------------------------------------------------------+
                   |                                       |                                   |
                   v                                       v                                   v
        +--------------------+                   +-------------------+               +-------------------+
        | PostgreSQL 16 DB   |                   | Redis 7 Queue     |               | Immutable Storage |
        | - All Money Paise  |                   | - Async Ingestion |               | - S3 / Local Dev  |
        | - Tenant Isolation |                   | - Task Broker     |               | - SHA-256 Hashed  |
        +--------------------+                   +-------------------+               +-------------------+
```

---

## Core Capabilities

### 1. Multi-Tenancy & Role-Based Access Control (RBAC)
- Multi-tier hierarchy: **CA Firm (Organization) > Users > Clients > Financial Years**.
- Strict row-level tenant isolation: `organization_id` enforced on every SQL query.
- Roles:
  - **Partner / CA**: Full authority to approve draft vouchers to `FINAL`, resolve exceptions, manage clients, export Tally Prime XML vouchers, and configure firm rules.
  - **Article / Staff**: Access to review documents, edit extracted fields, and draft vouchers. **Cannot finalize entries without CA Partner review.**
  - **Read-Only**: Client auditors or compliance observers.
- Password hashing with **Argon2**, session management, and optional **TOTP 2FA**.

### 2. Document Intake & Processing Pipeline
- Handles PDF, JPG, PNG, and Bank Statement CSV/XLSX.
- Immutably stores originals alongside a **SHA-256 hash** to immediately detect duplicate re-uploads.
- Pipeline stages:
  $$\text{Upload} \longrightarrow \text{Classify} \longrightarrow \text{Extract} \longrightarrow \text{Validate} \longrightarrow \text{Categorise} \longrightarrow \text{Draft Entry}$$
- Normalized bounding boxes (`[ymin, xmin, ymax, xmax]`) and confidence scores stored per field for visual overlay in the split-pane UI.

### 3. Deterministic Validation Engine (No LLM Hallucinations)
All compliance and tax validation logic is written in deterministic Python code:
- **GSTIN Format & Checksum**: Validates the 15-character statutory format and calculates check digit using the **Luhn Mod-36** algorithm.
- **Tax Logic**:
  - *Supplier State == Place of Supply* $\Rightarrow$ Intra-state $\Rightarrow$ Equal CGST + SGST (Flags error if IGST charged).
  - *Supplier State != Place of Supply* $\Rightarrow$ Inter-state $\Rightarrow$ IGST only (Flags error if CGST/SGST charged).
- **Statutory Rate Slabs**: Validates $0\%, 0.1\%, 0.25\%, 1.5\%, 3\%, 5\%, 12\%, 18\%, 28\% + \text{cess}$, with sanity checks against known HSN codes (e.g. 9983 IT Services $\rightarrow 18\%$).
- **Arithmetic Integrity**: Verifies line item sum equals taxable value and validates tax amounts within a $₹1.00$ rounding tolerance ($100 \text{ paise}$).
- **Section 16(4) Time-Bar**: Flags invoices where ITC claim deadline (30th November following financial year end) has elapsed.
- **Section 17(5) Blocked Credit**: Identifies blocked categories (food/catering, motor vehicles, employee perks, gym memberships, works contract) and marks credit as ineligible for CA review.
- **Duplicate Detection**: Identifies exact duplicates (same vendor GSTIN + invoice number + FY) and fuzzy duplicates (same amount + vendor + close date).

### 4. Continuous Learning Categorisation Engine
Resolves chart of account ledgers in strict order:
1. **Learned Rules**: Past manual corrections by CA Partners automatically create and update client rules ($Vendor \rightarrow Ledger$).
2. **Vendor-Based Rules**: Pattern and keyword matching.
3. **HSN/SAC Mapping & LLM Heuristics**: Suggested ledger with confidence score.

### 5. Multi-Way Reconciliation Engine
- **GSTR-2B vs Books**:
  - Parsers for both GST Portal **JSON** and **Excel (.xlsx)** formats.
  - Multi-pass matcher: Exact match $\rightarrow$ Tolerant match (normalizes `/`, `-`, leading zeroes, date window, amount tolerance) $\rightarrow$ In books not in 2B $\rightarrow$ In 2B not in books $\rightarrow$ Duplicates.
  - Computes eligible, at risk, and blocked ITC with a **Defaulting Vendor Follow-up List**.
- **Bank Reconciliation**:
  - Matches bank lines against ledger vouchers using amount, date clearance windows, UTR/cheque reference numbers, and narration keywords.

### 6. Primary Screen: Prioritised Exception Queue
- Prioritized by severity (`High`, `Medium`, `Low`), client, amount, and age.
- Plain-language statutory reason, deterministic evidence, and suggested fix.
- Interactive **Split-Pane Review**: Source invoice on the left with interactive bounding boxes; editable fields and ledger mapping on the right.
- **CA Approval Gate**: Entries change status from `draft` to `final` **only** upon Partner approval.

### 7. Reports & Tally Prime XML Export
- Formatted **Trial Balance** (verified debits equal credits), **Day Book**, and **GSTR-3B Liability Working**.
- One-click export to **Tally Prime compatible XML**: standard accounting vouchers (`<ENVELOPE>`) ready for direct import into Tally Prime.
- Export to Excel (`.xlsx`) and PDF.

### 8. India DPDP Act Compliance & Data Protection
- **Field-Level Encryption**: Sensitive identifiers (PAN, GSTIN, Bank Accounts) encrypted at rest using AES-256 (Fernet).
- **Strict Privacy**: Zero client accounting data is ever used to train AI models.
- **Audit Trail**: Immutable audit logs capturing every user login, AI draft, CA edit, approval, and export.
- **Expiring Portal Upload Links**: Token-authenticated upload link (`/portal/upload/:token`) allowing clients to drop bills without logging in.

---

## Quick Start (Docker Compose)

### Prerequisites
- Docker & Docker Compose (v2+)

### Run Accuro in One Command:
```bash
# Clone and enter workspace
git clone https://github.com/accuro-ca/accuro.git
cd accuro

# Copy environment variables
cp .env.example .env

# Start all Accuro microservices
docker compose up -d --build
```

### Access Services:
- **Frontend Web Console**: [http://localhost:3000](http://localhost:3000)
- **FastAPI Interactive Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## Pre-Seeded Demo Credentials

The database auto-seeds a realistic demo firm (*"Mehta & Associates, Chartered Accountants"*, FRN: `105642W`) with 3 realistic Indian clients and ~100 invoices:

| Role | Email | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **CA Partner** | `partner@mehta-ca.in` | `Partner@Accuro2025!` | Full approval, finalise, Tally export, client setup |
| **Article Staff** | `article@mehta-ca.in` | `Article@Accuro2025!` | Review, edit, draft vouchers (cannot approve/finalise) |

*Tip: The login page includes 1-click quick login buttons for both accounts.*

### Demo Clients:
1. **Apex Retailers Private Limited** (`27AABCA1234F1Z5` - Maharashtra)
2. **Zenith Technologies LLP** (`29AABCZ9876K1Z2` - Karnataka)
3. **Bharat Logistics & Freight Solutions** (`07AAACB5555L1Z8` - Delhi)

---

## Local Development (Without Docker)

### Backend Setup:
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
python -c "from app.db.seed_data import seed_database; seed_database()"
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend Setup:
```bash
cd frontend
npm install
npm run dev
```

### Running Automated Test Suite:
```bash
cd backend
pytest -v
```

---

## Explicitly Out of Scope

As required for CA firm risk compliance:
1. **Direct Portal Filing & Signing**: Accuro drafts first passes and prepares reconciliation workings; actual statutory filing to the GSTN/Income Tax portal and digital signature (DSC) signing must be executed directly by the licensed CA.
2. **Live GSTR-2B Fetch via GSP**: Live API fetching from GSTN requires a licensed GST Suvidha Provider (GSP). Accuro implements the extensible `GSTDataProvider` interface using `FileImportProvider` (supporting JSON and Excel). A stub is provided for future GSP integration.
