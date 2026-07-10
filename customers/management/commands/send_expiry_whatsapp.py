# # # ----whtspp meta
from django.core.management.base import BaseCommand
from datetime import date, timedelta
from pathlib import Path
import time

from django.conf import settings

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
)
from reportlab.lib.styles import getSampleStyleSheet

from customers.utils import get_today_expiring_customers

from customers.management.commands.whatsapp import (
    send_whatsapp_message,
)

class Command(BaseCommand):

    help = "Send WhatsApp expiry alerts"

    def handle(self, *args, **kwargs):

        # TESTING
        # Get all expiring customers
        customers = get_today_expiring_customers()

        if not customers:
            self.stdout.write("No expiring customers today.")
            return

        from_date = date.today()
        to_date = from_date + timedelta(days=1)

        from_date_str = from_date.strftime("%d %b %Y")
        to_date_str = to_date.strftime("%d %b %Y")

        lco_map = {}

        for customer in customers:

            if not customer.lco or not customer.lco.phone:
                continue

            phone = (
                customer.lco.phone
                .replace("+", "")
                .replace(" ", "")
            )

            if not phone.startswith("91"):
                phone = f"91{phone}"

            if phone not in lco_map:
                lco_map[phone] = {
                    "lco_name": customer.lco.name,
                    "customers": []
                }

            lco_map[phone]["customers"].append(customer)

        # -------------------------------------------------------

        for phone, data in lco_map.items():

            lco_name = data["lco_name"]
            custs = data["customers"]

            customer_lines = []

            # -------------------------------
            # Generate PDF
            # -------------------------------

            reports_dir = Path(settings.MEDIA_ROOT) / "expiry_reports"
            reports_dir.mkdir(parents=True, exist_ok=True)

            pdf_name = f"expiry_{phone}_{date.today()}.pdf"

            pdf_path = reports_dir / pdf_name

            doc = SimpleDocTemplate(str(pdf_path))

            styles = getSampleStyleSheet()

            content = []

            content.append(
                Paragraph(
                    f"<b>Expiry Report ({from_date_str} - {to_date_str})</b>",
                    styles["Title"]
                )
            )

            content.append(
                Paragraph(
                    f"LCO : {lco_name}",
                    styles["Heading2"]
                )
            )

            content.append(Spacer(1, 20))

            for i, c in enumerate(custs, start=1):

                pdf_text = f"""
                <b>{i}. {c.full_name}</b><br/>
                Phone : {c.phone}<br/>
                Username : {c.username}<br/>
                ISP : {c.isp.name if c.isp else "-"}<br/><br/>
                Expiry Date : {c.expiry_date.strftime('%d %b %Y') if c.expiry_date else "-"}<br/><br/>
                """

                content.append(
                    Paragraph(
                        pdf_text,
                        styles["BodyText"]
                    )
                )

                customer_lines.append(
                    f"{i}. {c.full_name or '-'} | "
                    f"Phone: {c.phone or '-'} | "
                    f"User: {c.username or '-'} | "
                    f"ISP: {c.isp.name if c.isp else '-'}"
                )

            doc.build(content)

            pdf_url = (
                f"{settings.SITE_URL}"
                f"{settings.MEDIA_URL}"
                f"expiry_reports/{pdf_name}"
            )

            print("\nPDF URL:", pdf_url)

            # -------------------------------
            # First Template
            # -------------------------------

            template_result = send_whatsapp_message(
                phone=phone,
                lco_name=lco_name,
                date_str=f"{from_date_str} - {to_date_str}",
                customer_list=(
                    f"{len(customer_lines)} customer(s) nearing expiry. "
                    f"Complete customer report: {pdf_url}"
                )
            )

            print(template_result)

            if not template_result:
                continue

            

            self.stdout.write(
                self.style.SUCCESS(
                    f"WhatsApp sent to {phone}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "WhatsApp alerts process completed"
            )
        )


# for document sending---


# from django.core.management.base import BaseCommand
# from datetime import date
# from pathlib import Path

# from django.conf import settings

# from reportlab.platypus import (
#     SimpleDocTemplate,
#     Paragraph,
#     Spacer,
#     PageBreak
# )
# from reportlab.lib.styles import getSampleStyleSheet

# from customers.utils import get_today_expiring_customers

# from customers.management.commands.whatsapp import (
#     send_whatsapp_message,
#     send_whatsapp_document
# )


# class Command(BaseCommand):

#     help = "Send WhatsApp expiry alerts with PDF report"

#     def handle(self, *args, **kwargs):

#         # customers = get_today_expiring_customers()
#         customers = get_today_expiring_customers().filter(
#             lco_id=3
#         )

#         if not customers:
#             self.stdout.write("No expiring customers today.")
#             return

#         today_str = date.today().strftime("%d %b %Y")

#         lco_map = {}

#         for customer in customers:

#             if not customer.lco:
#                 continue

#             phone = customer.lco.phone

#             if not phone:
#                 continue

#             phone = phone.replace("+", "").replace(" ", "")

#             if not phone.startswith("91"):
#                 phone = f"91{phone}"

#             if phone not in lco_map:

#                 lco_map[phone] = {
#                     "lco_name": customer.lco.name,
#                     "customers": []
#                 }

#             lco_map[phone]["customers"].append(customer)

#         for phone, data in lco_map.items():

#             lco_name = data["lco_name"]
#             custs = data["customers"]

#             # ---------------------------------
#             # Create PDF
#             # ---------------------------------

#             reports_dir = Path(settings.MEDIA_ROOT) / "expiry_reports"
#             reports_dir.mkdir(parents=True, exist_ok=True)

#             pdf_name = (
#                 f"expiry_{phone}_{date.today()}.pdf"
#             )

#             pdf_path = reports_dir / pdf_name

#             doc = SimpleDocTemplate(str(pdf_path))

#             styles = getSampleStyleSheet()

#             content = []

#             content.append(
#                 Paragraph(
#                     f"Expiry Report - {today_str}",
#                     styles["Title"]
#                 )
#             )

#             content.append(
#                 Paragraph(
#                     f"LCO : {lco_name}",
#                     styles["Heading2"]
#                 )
#             )

#             content.append(Spacer(1, 20))

#             for i, c in enumerate(custs, start=1):

#                 customer_text = f"""
#                 <b>{i}. {c.full_name or '-'}</b><br/>
#                 Phone: {c.phone or '-'}<br/>
#                 Username: {c.username or '-'}<br/>
#                 ISP: {c.isp.name if c.isp else '-'}<br/>
#                 """

#                 content.append(
#                     Paragraph(
#                         customer_text,
#                         styles["BodyText"]
#                     )
#                 )

#                 content.append(Spacer(1, 10))

#             doc.build(content)

#             # ---------------------------------
#             # Send template
#             # ---------------------------------

#             template_result = send_whatsapp_message(
#                 phone=phone,
#                 lco_name=lco_name,
#                 date_str=today_str,
#                 customer_list=f"{len(custs)} customer(s) nearing expiry. Please see attached report."
#             )

#             print("TEMPLATE RESULT:")
#             print(template_result)

#             # ---------------------------------
#             # Send PDF
#             # ---------------------------------

#             pdf_url = (
#                 f"{settings.SITE_URL}"
#                 f"{settings.MEDIA_URL}"
#                 f"expiry_reports/{pdf_name}"
#             )
#             print("\n===== PDF DEBUG =====")
#             print("PDF PATH:", pdf_path)
#             print("PDF EXISTS:", pdf_path.exists())
#             print("PDF URL:", pdf_url)
#             print("=====================\n")

#             # document_result = send_whatsapp_document(
#             #     phone=phone,
#             #     document_url=pdf_url,
#             #     filename=pdf_name
#             # )
#             document_result = send_whatsapp_document(
#                 phone=phone,
#                 document_url="https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
#                 filename="test.pdf"
#             )

#             print("DOCUMENT RESULT:")
#             print(document_result)

#             self.stdout.write(
#                 self.style.SUCCESS(
#                     f"Report sent to {phone}"
#                 )
#             )