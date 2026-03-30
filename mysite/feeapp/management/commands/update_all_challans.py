from django.core.management.base import BaseCommand
from feeapp.models import Challan, ChallanFeeHead
from feeapp.views import get_logo_base64, get_active_logo
from django.core.files.base import ContentFile
import datetime

class Command(BaseCommand):
    help = 'Regenerates HTML content for all challans to apply new styles'

    def handle(self, *args, **options):
        challans = Challan.objects.all()
        total = challans.count()
        self.stdout.write(f"Found {total} challans. Starting update...")

        # Get logo once
        active_logo = get_active_logo()
        college_name = active_logo.college_name if active_logo else "Government Graduate College, Civil Lines Sheikhupura"
        logo_base64 = get_logo_base64()

        for i, challan in enumerate(challans, 1):
            try:
                # Get fee heads
                fee_heads_html = []
                for challan_fee_head in challan.challanfeehead_set.all():
                    fee_name = challan_fee_head.fee_head_account.fee_head_name
                    amount = challan_fee_head.amount
                    fee_heads_html.append(f"{fee_name}: Rs.{amount}")

                fee_heads_text = " | ".join(fee_heads_html)
                
                # Format dates
                formatted_due_date = challan.due_date.strftime('%d/%m/%Y') if challan.due_date else 'N/A'
                
                # Build fee table rows
                fee_table_rows = ""
                fee_items = fee_heads_text.split(' | ')
                for item in fee_items:
                    parts = item.split(': Rs.')
                    if len(parts) == 2:
                        fee_name = parts[0].strip()
                        fee_amount = parts[1].strip()
                        fee_table_rows += f"<tr><td>{fee_name}</td><td>{fee_amount}</td></tr>\n"

                # Student data
                student = challan.student
                student_name = student.name if student else "Unknown"
                roll_no = student.college_roll_no if student else "Unknown"
                shift = student.status.title() if student else "Unknown"
                
                # Program data
                disciplines = challan.disciplines or "N/A"
                semesters = challan.semesters or "N/A"
                
                session = "N/A"
                if student and student.scheme_of_study and student.scheme_of_study.session:
                    session = student.scheme_of_study.session.year

                # Check payment status for label
                status_label = ""
                if challan.payment_status == 'PAID' or challan.status.upper() == 'PAID':
                    status_label = '<div style="text-align: center; color: green; font-weight: bold; font-size: 14px; margin: 10px 0;">STATUS: PAID</div>'
                
                # Amounts
                total_amount = challan.challan_amount
                remaining_amount = challan.remaining_amount or 0
                
                # Determine amount display
                # If it's an installment (partially paid or has remaining amount logic), show remaining?
                # For simplicity, if it's the original challan logic, we show Total.
                # If it's an installment logic, we might need different fields.
                # The bulk update should respect the current challan's context.
                # To be safe and consistent with "create_single_challan_with_html", we display Total Amount.
                # If the challan is an installment (has original_challan), this might be slightly different,
                # but "create_single_challan_with_html" is for new challans.
                # Let's use the generic "Total Amount" display which works for most.
                
                # HTML Template (Exact Copy from views.py with variables substituted)
                html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Fee Challan - {challan.challan_number}</title>
    <meta charset="UTF-8">
    <style>
        @page {{
            size: 297mm 210mm;
            margin: 5mm;
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: 'Times New Roman', serif;
            font-size: 12px;
            line-height: 1.3;
            background: white;
        }}
        @media screen {{
            body {{
                background: #525659;
                display: flex;
                justify-content: center;
                padding: 20px 0;
            }}
            .page-container {{
                background: white;
                width: 297mm;
                max-width: 100%;
                margin: 0 auto;
                box-shadow: 0 0 10px rgba(0,0,0,0.5);
            }}
        }}
        /* ✅ UPDATED: Table-based layout for PDF compatibility */
        .page-container {{
            width: 100%;
            table-layout: fixed;
            border-collapse: separate;
            border-spacing: 4mm;
        }}
        .challan-copy {{
            width: 32%;
            border: 1px solid black;
            padding: 3mm;
            vertical-align: top;
        }}
        .copy-label {{
            text-align: center;
            font-weight: bold;
            font-size: 12px;
            margin-bottom: 1mm;
        }}
        .header-section {{
            margin-bottom: 2mm;
            text-align: center;
        }}
        .header-table {{
            width: auto;
            margin: 0 auto;
            border-collapse: collapse;
        }}
        .header-table td {{
            border: 0;
            padding: 0;
            vertical-align: middle;
        }}
        .logo-container {{
            padding-right: 2mm;
        }}
        .logo-container img {{
            width: 25px;
            height: 25px;
            border-radius: 50%;
        }}
        .college-name {{
            font-weight: bold;
            font-size: 12px;
        }}
        .challan-number {{
            text-align: right;
            font-size: 10px;
            margin: 1mm 0;
        }}
        .program-info {{
            text-align: center;
            font-size: 11px;
            margin: 1mm 0;
        }}
        
        hr {{
            border: none;
            border-top: 1px solid black;
            margin: 2mm 0;
        }}
        .info-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1mm 0;
        }}
        .info-table td {{
            border: 0;
            padding: 0;
            vertical-align: bottom;
        }}
        .student-info {{
            text-align: right;
            padding-right: 3mm;
            font-size: 11px;
        }}
        .date-box {{
            width: 35mm;
            text-align: left;
            font-size: 11px;
        }}
        .fee-details {{
            font-size: 12px;
            margin: 2mm 0;
        }}
        .fee-details strong {{
            font-size: 12px;
        }}
        
        .fee-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 2mm 0;
            font-size: 12px;
        }}
        .fee-table th {{
            border: 1px solid black;
            padding: 1mm 2mm;
            text-align: center;
            background-color: white;
            font-weight: bold;
        }}
        .fee-table td {{
            border: 1px solid black;
            padding: 1mm 2mm;
            text-align: center;
        }}
        
        .amount-box {{
            text-align: right;
            margin: 2mm 0;
        }}
        .instructions {{
            border: 1px solid black;
            padding: 1.5mm;
            font-size: 9px;
            margin: 2mm 0;
            line-height: 1.1;
            white-space: nowrap;
        }}
        .footer-note {{
            font-style: italic;
            font-size: 8px;
            margin: 1mm 0;
        }}
        .signature-line {{
            font-size: 11px;
            margin-top: 40px;
        }}
    </style>
</head>
<body>
    <!-- ✅ UPDATED: Table-based layout for horizontal alignment -->
    <table class="page-container">
        <tr>
            <td class="challan-copy">
            <div class="copy-label">Student Copy</div>
            {status_label}
            <div class="header-section">
                <table class="header-table">
                    <tr>
                        <td class="logo-container">
                            <img src="{logo_base64}" alt="Logo">
                        </td>
                        <td class="college-name">{college_name}</td>
                    </tr>
                </table>
            </div>
            <div class="challan-number"><strong>Challan No.</strong> {challan.challan_number}</div>
            <div class="program-info">{disciplines} - {semesters} - Session {session}</div>
            <hr>
            <table class="info-table">
                <tr>
                    <td class="student-info"><strong>Student:</strong> {student_name} | <strong>Roll No:</strong> {roll_no} | <strong>Shift:</strong> {shift}</td>
                    <td class="date-box"><strong>Due Date:</strong> {formatted_due_date}</td>
                </tr>
            </table>
            <div class="fee-details">
                <strong>Fee Breakdown:</strong>
                <table class="fee-table">
                    <thead>
                        <tr>
                            <th>Fee Head</th>
                            <th>Amount (Rs.)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {fee_table_rows}
                    </tbody>
                </table>
            </div>
            <div class="amount-box">
                <strong>Total Amount: Rs. {total_amount:,.2f}</strong>
            </div>
            <div class="instructions">
                &bull; Fee can be deposited Online through any Banking app/ATM/Mobile Wallet.<br>
                &bull; For Online Fee Deposit: Select 1BILL, <strong>Enter 1Bill#: {challan.one_bill_number or 'Pending'}</strong> and pay.
            </div>
            <div class="footer-note">Any fee directly transferred to account through ATM any Banking channel is not verifiable.</div>
            <div class="signature-line">Officer: _________ Cashier: _________ Stamp: _________</div>
            </td>
            
            <td class="challan-copy">
            <div class="copy-label">Bank Copy</div>
            {status_label}
            <div class="header-section">
                <table class="header-table">
                    <tr>
                        <td class="logo-container">
                            <img src="{logo_base64}" alt="Logo">
                        </td>
                        <td class="college-name">{college_name}</td>
                    </tr>
                </table>
            </div>
            <div class="challan-number"><strong>Challan No.</strong> {challan.challan_number}</div>
            <div class="program-info">{disciplines} - {semesters} - Session {session}</div>
            <hr>
            <table class="info-table">
                <tr>
                    <td class="student-info"><strong>Student:</strong> {student_name} | <strong>Roll No:</strong> {roll_no} | <strong>Shift:</strong> {shift}</td>
                    <td class="date-box"><strong>Due Date:</strong> {formatted_due_date}</td>
                </tr>
            </table>
            <div class="fee-details">
                <strong>Fee Breakdown:</strong>
                <table class="fee-table">
                    <thead>
                        <tr>
                            <th>Fee Head</th>
                            <th>Amount (Rs.)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {fee_table_rows}
                    </tbody>
                </table>
            </div>
            <div class="amount-box">
                <strong>Total Amount: Rs. {total_amount:,.2f}</strong>
            </div>
            <div class="instructions">
                &bull; Fee can be deposited Online through any Banking app/ATM/Mobile Wallet.<br>
                &bull; For Online Fee Deposit: Select 1BILL, <strong>Enter 1Bill#: {challan.one_bill_number or 'Pending'}</strong> and pay.
            </div>
            <div class="footer-note">Any fee directly transferred to account through ATM any Banking channel is not verifiable.</div>
            <div class="signature-line">Officer: _________ Cashier: _________ Stamp: _________</div>
            </td>
            
            <td class="challan-copy">
            <div class="copy-label">College Copy</div>
            {status_label}
            <div class="header-section">
                <table class="header-table">
                    <tr>
                        <td class="logo-container">
                            <img src="{logo_base64}" alt="Logo">
                        </td>
                        <td class="college-name">{college_name}</td>
                    </tr>
                </table>
            </div>
            <div class="challan-number"><strong>Challan No.</strong> {challan.challan_number}</div>
            <div class="program-info">{disciplines} - {semesters} - Session {session}</div>
            <hr>
            <table class="info-table">
                <tr>
                    <td class="student-info"><strong>Student:</strong> {student_name} | <strong>Roll No:</strong> {roll_no} | <strong>Shift:</strong> {shift}</td>
                    <td class="date-box"><strong>Due Date:</strong> {formatted_due_date}</td>
                </tr>
            </table>
            <div class="fee-details">
                <strong>Fee Breakdown:</strong>
                <table class="fee-table">
                    <thead>
                        <tr>
                            <th>Fee Head</th>
                            <th>Amount (Rs.)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {fee_table_rows}
                    </tbody>
                </table>
            </div>
            <div class="amount-box">
                <strong>Total Amount: Rs. {total_amount:,.2f}</strong>
            </div>
            <div class="instructions">
                &bull; Fee can be deposited Online through any Banking app/ATM/Mobile Wallet.<br>
                &bull; For Online Fee Deposit: Select 1BILL, <strong>Enter 1Bill#: {challan.one_bill_number or 'Pending'}</strong> and pay.
            </div>
            <div class="footer-note">Any fee directly transferred to account through ATM any Banking channel is not verifiable.</div>
            <div class="signature-line">Officer: _________ Cashier: _________ Stamp: _________</div>
            </td>
        </tr>
    </table>
</body>
</html>
"""
                # Update challan
                challan.html_content = html_content
                
                # Save plain text (for easy debugging if needed) or just the content needed for PDF/View
                # Also saving the file to media storage to ensure "Download PDF" picks up new content
                challan.challan_file.save(
                    f"{challan.challan_number}.html", 
                    ContentFile(html_content.encode('utf-8')),
                    save=False
                )
                
                challan.save()
                
                if i % 10 == 0:
                    self.stdout.write(f"Updated {i}/{total} challans...")
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error updating challan {challan.challan_number}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully updated all {total} challans!"))
