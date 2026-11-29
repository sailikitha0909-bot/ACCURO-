import csv
import io
from datetime import datetime, timezone
from typing import List, Dict, Any
import openpyxl

class BankParser:
    @staticmethod
    def parse_csv(content: str | bytes) -> List[Dict[str, Any]]:
        """Parse standard Indian bank statement CSV."""
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors='ignore')
        
        reader = csv.reader(io.StringIO(content))
        lines = []
        rows = list(reader)

        header_idx = None
        col_map = {}
        for r_idx, row in enumerate(rows):
            row_lower = [c.lower().strip() for c in row]
            if any("date" in c for c in row_lower) and (any("debit" in c or "withdrawal" in c for c in row_lower) or any("credit" in c or "deposit" in c for c in row_lower)):
                header_idx = r_idx
                for c_idx, col in enumerate(row_lower):
                    if "txn" in col or "transaction date" in col or "date" in col and "val" not in col:
                        if "date" not in col_map: col_map["date"] = c_idx
                    elif "val" in col and "date" in col: col_map["val_date"] = c_idx
                    elif "narration" in col or "description" in col or "particulars" in col or "details" in col: col_map["narration"] = c_idx
                    elif "ref" in col or "chq" in col or "utr" in col or "cheque" in col: col_map["ref"] = c_idx
                    elif "debit" in col or "withdrawal" in col or "dr" in col: col_map["debit"] = c_idx
                    elif "credit" in col or "deposit" in col or "cr" in col: col_map["credit"] = c_idx
                    elif "balance" in col: col_map["balance"] = c_idx
                break

        if header_idx is None:
            return lines

        for row in rows[header_idx + 1:]:
            if not row or len(row) <= max(col_map.values(), default=0):
                continue

            date_str = row[col_map.get("date", 0)].strip()
            if not date_str:
                continue

            txn_date = None
            for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%b-%Y"):
                try:
                    txn_date = datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
                    break
                except Exception:
                    pass
            if not txn_date:
                continue

            def clean_amount(val_str: str) -> int:
                if not val_str:
                    return 0
                cleaned = val_str.replace(",", "").replace("INR", "").replace("Rs.", "").strip()
                try:
                    return int(round(float(cleaned) * 100))
                except Exception:
                    return 0

            debit_p = clean_amount(row[col_map["debit"]]) if "debit" in col_map else 0
            credit_p = clean_amount(row[col_map["credit"]]) if "credit" in col_map else 0
            balance_p = clean_amount(row[col_map["balance"]]) if "balance" in col_map else 0

            lines.append({
                "txn_date": txn_date,
                "narration": row[col_map.get("narration", 1)].strip() if "narration" in col_map else "",
                "reference_no": row[col_map.get("ref", 2)].strip() if "ref" in col_map else "",
                "debit_paise": debit_p,
                "credit_paise": credit_p,
                "balance_paise": balance_p,
            })

        return lines
