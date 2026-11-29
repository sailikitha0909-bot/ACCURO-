import io
from datetime import datetime
from typing import List, Dict, Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class ExportService:
    @staticmethod
    def generate_tally_xml(entries: List[Any], company_name: str = "Client Company") -> str:
        """
        Generate Tally Prime compatible XML vouchers for direct import into Tally.
        Strictly complies with Tally XML schema for accounting vouchers.
        """
        xml_lines = [
            '<?xml version="1.0" encoding="utf-8"?>',
            '<ENVELOPE>',
            '  <HEADER>',
            '    <TALLYREQUEST>Import Data</TALLYREQUEST>',
            '  </HEADER>',
            '  <BODY>',
            '    <IMPORTDATA>',
            '      <REQUESTDESC>',
            '        <REPORTNAME>Vouchers</REPORTNAME>',
            '        <STATICVARIABLES>',
            f'          <SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>',
            '        </STATICVARIABLES>',
            '      </REQUESTDESC>',
            '      <REQUESTDATA>',
        ]

        for entry in entries:
            inv_date = entry.invoice_date.strftime("%Y%m%d") if entry.invoice_date else datetime.now().strftime("%Y%m%d")
            inv_num = entry.invoice_number or "VCH-001"
            party_name = entry.party_name or "Sundry Creditor"
            vch_type = "Purchase" if entry.entry_type == "purchase" else "Sales"

            total_rs = entry.total_amount_paise / 100.0
            taxable_rs = entry.taxable_value_paise / 100.0
            cgst_rs = entry.cgst_paise / 100.0
            sgst_rs = entry.sgst_paise / 100.0
            igst_rs = entry.igst_paise / 100.0
            round_off_rs = entry.round_off_paise / 100.0

            expense_ledger = "Software & SaaS Subscriptions"
            if entry.debit_account:
                expense_ledger = entry.debit_account.account_name

            xml_lines.extend([
                '        <TALLYMESSAGE xmlns:UDF="TallyUDF">',
                f'          <VOUCHER VCHTYPE="{vch_type}" ACTION="Create" OBJVIEW="AccountingVoucherView">',
                f'            <DATE>{inv_date}</DATE>',
                f'            <VOUCHERTYPENAME>{vch_type}</VOUCHERTYPENAME>',
                f'            <VOUCHERNUMBER>{inv_num}</VOUCHERNUMBER>',
                f'            <REFERENCE>{inv_num}</REFERENCE>',
                f'            <PARTYLEDGERNAME>{party_name}</PARTYLEDGERNAME>',
                f'            <NARRATION>AI-prepared draft by Accuro. Requires CA review. Ref #{inv_num} GSTIN: {entry.party_gstin or "N/A"}</NARRATION>',
                '            <!-- Party Ledger Entry (Credit for Purchase) -->',
                '            <ALLLEDGERENTRIES.LIST>',
                f'              <LEDGERNAME>{party_name}</LEDGERNAME>',
                '              <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>',
                f'              <AMOUNT>{total_rs:.2f}</AMOUNT>',
                '            </ALLLEDGERENTRIES.LIST>',
                '            <!-- Expense Ledger Entry (Debit for Purchase) -->',
                '            <ALLLEDGERENTRIES.LIST>',
                f'              <LEDGERNAME>{expense_ledger}</LEDGERNAME>',
                '              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>',
                f'              <AMOUNT>-{taxable_rs:.2f}</AMOUNT>',
                '            </ALLLEDGERENTRIES.LIST>',
            ])

            # Add Tax Ledgers if applicable
            if cgst_rs > 0:
                xml_lines.extend([
                    '            <ALLLEDGERENTRIES.LIST>',
                    '              <LEDGERNAME>Input CGST</LEDGERNAME>',
                    '              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>',
                    f'              <AMOUNT>-{cgst_rs:.2f}</AMOUNT>',
                    '            </ALLLEDGERENTRIES.LIST>',
                ])
            if sgst_rs > 0:
                xml_lines.extend([
                    '            <ALLLEDGERENTRIES.LIST>',
                    '              <LEDGERNAME>Input SGST</LEDGERNAME>',
                    '              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>',
                    f'              <AMOUNT>-{sgst_rs:.2f}</AMOUNT>',
                    '            </ALLLEDGERENTRIES.LIST>',
                ])
            if igst_rs > 0:
                xml_lines.extend([
                    '            <ALLLEDGERENTRIES.LIST>',
                    '              <LEDGERNAME>Input IGST</LEDGERNAME>',
                    '              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>',
                    f'              <AMOUNT>-{igst_rs:.2f}</AMOUNT>',
                    '            </ALLLEDGERENTRIES.LIST>',
                ])
            if round_off_rs != 0:
                sign = "-" if round_off_rs > 0 else ""
                xml_lines.extend([
                    '            <ALLLEDGERENTRIES.LIST>',
                    '              <LEDGERNAME>Round Off</LEDGERNAME>',
                    f'              <ISDEEMEDPOSITIVE>{"Yes" if round_off_rs > 0 else "No"}</ISDEEMEDPOSITIVE>',
                    f'              <AMOUNT>{sign}{abs(round_off_rs):.2f}</AMOUNT>',
                    '            </ALLLEDGERENTRIES.LIST>',
                ])

            xml_lines.extend([
                '          </VOUCHER>',
                '        </TALLYMESSAGE>',
            ])

        xml_lines.extend([
            '      </REQUESTDATA>',
            '    </IMPORTDATA>',
            '  </BODY>',
            '</ENVELOPE>',
        ])

        return "\n".join(xml_lines)

    @staticmethod
    def generate_excel_report(report_type: str, data: Dict[str, Any], client_name: str) -> io.BytesIO:
        """Create formatted Excel spreadsheet with deep-blue branding."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = report_type.replace("_", " ").title()[:30]

        # Branding Header
        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        title_font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
        sub_font = Font(name="Calibri", size=10, italic=True, color="E2E8F0")

        ws.merge_cells("A1:G1")
        ws["A1"] = f"ACCURO — {ws.title.upper()} — {client_name.upper()}"
        ws["A1"].font = title_font
        ws["A1"].fill = header_fill
        ws["A1"].alignment = Alignment(horizontal="center", vertical="center")

        ws.merge_cells("A2:G2")
        ws["A2"] = "Generated by Accuro | AI-prepared draft. Requires CA review."
        ws["A2"].font = sub_font
        ws["A2"].fill = header_fill
        ws["A2"].alignment = Alignment(horizontal="center", vertical="center")

        rows = data.get("rows", [])
        headers = data.get("headers", ["Date", "Particulars", "Voucher No", "Debit (₹)", "Credit (₹)"])

        # Table Column Headers
        col_header_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        col_header_font = Font(name="Calibri", size=11, bold=True, color="1E293B")
        
        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=4, column=col_idx, value=header)
            cell.font = col_header_font
            cell.fill = col_header_fill
            cell.alignment = Alignment(horizontal="center" if "date" in header.lower() or "no" in header.lower() else "left")

        current_row = 5
        for row_data in rows:
            for col_idx, val in enumerate(row_data, start=1):
                cell = ws.cell(row=current_row, column=col_idx, value=val)
                cell.font = Font(name="Calibri", size=10)
                if isinstance(val, (int, float)):
                    cell.number_format = '₹#,##0.00'
                    cell.alignment = Alignment(horizontal="right")
            current_row += 1

        # Auto-adjust column widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = col[0].column_letter
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    @staticmethod
    def generate_pdf_report(title: str, client_name: str, rows: List[List[str]], headers: List[str]) -> io.BytesIO:
        """Create clean printable PDF report with ReportLab."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        styles = getSampleStyleSheet()

        brand_style = ParagraphStyle(
            'BrandHeading',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=16,
            textColor=colors.HexColor("#1E3A8A"),
            spaceAfter=4,
        )
        sub_style = ParagraphStyle(
            'BrandSub',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=9,
            textColor=colors.HexColor("#475569"),
            spaceAfter=15,
        )

        elements = [
            Paragraph(f"ACCURO — {title.upper()}", brand_style),
            Paragraph(f"Client: {client_name} | AI-prepared draft by Accuro. Requires CA review.", sub_style),
            Spacer(1, 10),
        ]

        table_data = [headers] + rows
        t = Table(table_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ]))
        elements.append(t)
        doc.build(elements)
        buffer.seek(0)
        return buffer
