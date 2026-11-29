from datetime import datetime, date, timezone, timedelta
from typing import List, Dict, Any

class ComplianceCalendarService:
    @staticmethod
    def get_upcoming_deadlines(client_state: str = "27") -> List[Dict[str, Any]]:
        """
        Generate Indian tax statutory compliance calendar.
        Includes GSTR-1, GSTR-3B, TDS Payment (Challan 281), and Advance Tax.
        """
        today = date.today()
        deadlines = []

        # Current & Next month deadlines
        for month_offset in [0, 1]:
            target_year = today.year + ((today.month + month_offset - 1) // 12)
            target_month = ((today.month + month_offset - 1) % 12) + 1

            # 1. TDS Payment: 7th of every month
            tds_date = date(target_year, target_month, 7)
            deadlines.append({
                "title": "TDS Payment Deposit (Challan ITNS 281)",
                "category": "Direct Tax",
                "form": "Section 192 / 194C / 194J",
                "due_date": tds_date.isoformat(),
                "period": f"{(date(target_year, target_month, 1) - timedelta(days=1)).strftime('%B %Y')}",
                "status": "Overdue" if tds_date < today else ("Due Soon" if (tds_date - today).days <= 3 else "Upcoming")
            })

            # 2. GSTR-1: 11th of every month
            gstr1_date = date(target_year, target_month, 11)
            deadlines.append({
                "title": "GSTR-1 Monthly Return (Outward Supplies)",
                "category": "GST",
                "form": "GSTR-1",
                "due_date": gstr1_date.isoformat(),
                "period": f"{(date(target_year, target_month, 1) - timedelta(days=1)).strftime('%B %Y')}",
                "status": "Overdue" if gstr1_date < today else ("Due Soon" if (gstr1_date - today).days <= 3 else "Upcoming")
            })

            # 3. GSTR-3B: 20th of every month
            gstr3b_date = date(target_year, target_month, 20)
            deadlines.append({
                "title": "GSTR-3B Monthly Summary & ITC Settlement",
                "category": "GST",
                "form": "GSTR-3B",
                "due_date": gstr3b_date.isoformat(),
                "period": f"{(date(target_year, target_month, 1) - timedelta(days=1)).strftime('%B %Y')}",
                "status": "Overdue" if gstr3b_date < today else ("Due Soon" if (gstr3b_date - today).days <= 3 else "Upcoming")
            })

        # Advance Tax Installments: 15 June, 15 Sept, 15 Dec, 15 March
        current_year = today.year
        adv_dates = [
            (date(current_year, 6, 15), "1st Installment (15%)"),
            (date(current_year, 9, 15), "2nd Installment (45%)"),
            (date(current_year, 12, 15), "3rd Installment (75%)"),
            (date(current_year + 1, 3, 15), "4th Installment (100%)"),
        ]
        for dt, inst in adv_dates:
            if dt >= today - timedelta(days=30):
                deadlines.append({
                    "title": f"Advance Tax Payment — {inst}",
                    "category": "Income Tax",
                    "form": "Challan 280",
                    "due_date": dt.isoformat(),
                    "period": f"FY {current_year}-{str(current_year+1)[-2:]}",
                    "status": "Overdue" if dt < today else ("Due Soon" if (dt - today).days <= 7 else "Upcoming")
                })

        deadlines.sort(key=lambda x: x["due_date"])
        return deadlines

    @staticmethod
    def generate_missing_doc_reminders(
        client_name: str,
        vendor_name: str,
        missing_period: str,
        portal_upload_url: str
    ) -> Dict[str, str]:
        """
        Draft professional client communication in both Email and WhatsApp formats.
        Calm, precise tone per branding requirements.
        """
        email_subject = f"Document Request: Pending {vendor_name} Voucher for {missing_period} — {client_name}"
        
        email_body = f"""Dear {client_name} Team,

During our regular reconciliation pass for {missing_period}, Accuro identified that the purchase invoice/voucher from "{vendor_name}" has not yet been received in our books.

To ensure your Input Tax Credit (ITC) is accurately claimed and avoid potential GST interest or disallowance, please upload this invoice using your secure client upload link:
{portal_upload_url}

AI-prepared draft by Accuro. Requires CA review.
Mehta & Associates, Chartered Accountants"""

        whatsapp_body = (
            f"Hello {client_name}, Accuro noticed that the invoice from *{vendor_name}* for *{missing_period}* "
            f"is missing from our reconciliation records. Please upload it via your direct secure portal: {portal_upload_url} "
            f"to ensure full ITC claim in this month's GSTR-3B."
        )

        return {
            "email_subject": email_subject,
            "email_body": email_body,
            "whatsapp_message": whatsapp_body,
        }
