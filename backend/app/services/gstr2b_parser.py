import json
from datetime import datetime, timezone
from typing import List, Dict, Any
import openpyxl

class GSTR2BParser:
    @staticmethod
    def parse_json(json_content: str | bytes) -> List[Dict[str, Any]]:
        """Parse official GST Portal GSTR-2B JSON format."""
        if isinstance(json_content, bytes):
            json_content = json_content.decode('utf-8')
        
        data = json.loads(json_content)
        records: List[Dict[str, Any]] = []

        # Handle either root dict or enveloped data
        payload = data.get("data", data)
        b2b_list = payload.get("b2b", [])

        for supplier in b2b_list:
            ctin = supplier.get("ctin", "").strip().upper()
            cname = supplier.get("cname", "") or supplier.get("trade_name", "")
            
            for inv in supplier.get("inv", []):
                inum = inv.get("inum", "").strip()
                idt_str = inv.get("idt", "")
                
                # Parse date format dd-mm-yyyy or yyyy-mm-dd
                inv_date = None
                for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
                    try:
                        inv_date = datetime.strptime(idt_str, fmt).replace(tzinfo=timezone.utc)
                        break
                    except Exception:
                        pass
                if not inv_date:
                    inv_date = datetime.now(timezone.utc)

                itc_avl = inv.get("itcavl", "Y")
                itc_rzn = inv.get("itcrzn", "")

                tot_txval = 0
                tot_iamt = 0
                tot_camt = 0
                tot_samt = 0
                tot_csamt = 0

                for itm in inv.get("items", []):
                    # Values in paise
                    tot_txval += int(round(float(itm.get("txval", 0)) * 100))
                    tot_iamt += int(round(float(itm.get("iamt", 0)) * 100))
                    tot_camt += int(round(float(itm.get("camt", 0)) * 100))
                    tot_samt += int(round(float(itm.get("samt", 0)) * 100))
                    tot_csamt += int(round(float(itm.get("csamt", 0)) * 100))

                records.append({
                    "supplier_gstin": ctin,
                    "supplier_name": cname,
                    "invoice_number": inum,
                    "invoice_date": inv_date,
                    "taxable_value_paise": tot_txval,
                    "igst_paise": tot_iamt,
                    "cgst_paise": tot_camt,
                    "sgst_paise": tot_samt,
                    "cess_paise": tot_csamt,
                    "itc_availability": itc_avl,
                    "itc_reason": itc_rzn,
                })

        return records

    @staticmethod
    def parse_excel(file_path: str) -> List[Dict[str, Any]]:
        """Parse official GST Portal GSTR-2B Excel spreadsheet export."""
        wb = openpyxl.load_workbook(file_path, data_only=True)
        records: List[Dict[str, Any]] = []

        sheet_names = [s for s in wb.sheetnames if "b2b" in s.lower()]
        sheet = wb[sheet_names[0]] if sheet_names else wb.active

        # Find header row
        header_row_idx = None
        col_map = {}
        for row_idx, row in enumerate(sheet.iter_rows(values_only=True), start=1):
            row_str = [str(c or "").lower() for c in row]
            if any("gstin" in s for s in row_str) and any("invoice" in s for s in row_str):
                header_row_idx = row_idx
                for c_idx, col_name in enumerate(row):
                    if col_name:
                        norm = str(col_name).strip().lower()
                        if "gstin" in norm: col_map["gstin"] = c_idx
                        elif "legal name" in norm or "trade name" in norm: col_map["name"] = c_idx
                        elif "invoice number" in norm or "inum" in norm: col_map["inum"] = c_idx
                        elif "invoice date" in norm or "idt" in norm: col_map["idt"] = c_idx
                        elif "taxable value" in norm: col_map["txval"] = c_idx
                        elif "integrated tax" in norm or "igst" in norm: col_map["igst"] = c_idx
                        elif "central tax" in norm or "cgst" in norm: col_map["cgst"] = c_idx
                        elif "state" in norm and "tax" in norm: col_map["sgst"] = c_idx
                        elif "cess" in norm: col_map["cess"] = c_idx
                        elif "itc availability" in norm or "itc available" in norm: col_map["itc"] = c_idx
                        elif "reason" in norm: col_map["reason"] = c_idx
                break

        if not header_row_idx or "gstin" not in col_map:
            return records

        for row in sheet.iter_rows(min_row=header_row_idx + 1, values_only=True):
            gstin = str(row[col_map["gstin"]] or "").strip().upper()
            if not gstin or len(gstin) < 15:
                continue

            inum = str(row[col_map.get("inum", 0)] or "").strip()
            if not inum:
                continue

            idt_val = row[col_map.get("idt", 0)]
            if isinstance(idt_val, datetime):
                inv_date = idt_val.replace(tzinfo=timezone.utc)
            elif isinstance(idt_val, str):
                inv_date = None
                for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
                    try:
                        inv_date = datetime.strptime(idt_val.strip(), fmt).replace(tzinfo=timezone.utc)
                        break
                    except Exception:
                        pass
                if not inv_date:
                    inv_date = datetime.now(timezone.utc)
            else:
                inv_date = datetime.now(timezone.utc)

            def to_paise(val):
                try:
                    return int(round(float(val or 0) * 100))
                except Exception:
                    return 0

            records.append({
                "supplier_gstin": gstin,
                "supplier_name": str(row[col_map.get("name", 1)] or "").strip(),
                "invoice_number": inum,
                "invoice_date": inv_date,
                "taxable_value_paise": to_paise(row[col_map.get("txval", 0)] if "txval" in col_map else 0),
                "igst_paise": to_paise(row[col_map.get("igst", 0)] if "igst" in col_map else 0),
                "cgst_paise": to_paise(row[col_map.get("cgst", 0)] if "cgst" in col_map else 0),
                "sgst_paise": to_paise(row[col_map.get("sgst", 0)] if "sgst" in col_map else 0),
                "cess_paise": to_paise(row[col_map.get("cess", 0)] if "cess" in col_map else 0),
                "itc_availability": str(row[col_map.get("itc", 0)] or "Y").strip()[:1].upper(),
                "itc_reason": str(row[col_map.get("reason", 0)] or "").strip(),
            })

        return records
