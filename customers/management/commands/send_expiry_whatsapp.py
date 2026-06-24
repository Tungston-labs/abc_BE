

# # # ----whtspp meta


# from django.core.management.base import BaseCommand
# from datetime import date

# from customers.utils import get_today_expiring_customers
# from customers.management.commands.whatsapp import send_whatsapp_message


# class Command(BaseCommand):

#     help = "Send WhatsApp expiry alerts using Meta WhatsApp API"

#     def handle(self, *args, **kwargs):

#         customers = get_today_expiring_customers()

#         if not customers:
#             self.stdout.write("No expiring customers today.")
#             return

#         today_str = date.today().strftime("%d %b %Y")

#         # group by LCO
#         lco_map = {}

#         for customer in customers:
#             print(
#                 f"CUSTOMER={customer.full_name} | "
#                 f"LCO={customer.lco.name} | "
#                 f"LCO_PHONE={customer.lco.phone}"
#             )

#             if customer.lco and customer.lco.phone:

#                 phone = customer.lco.phone.replace("+", "").replace(" ", "")

#                 if not phone.startswith("91"):
#                     phone = f"91{phone}"

#                 if phone not in lco_map:
#                     lco_map[phone] = {
#                         "lco_name": customer.lco.name if customer.lco.name else "LCO",
#                         "customers": []
#                     }

#                 lco_map[phone]["customers"].append(customer)

#         # send messages
#         for phone, data in lco_map.items():

#             lco_name = data["lco_name"]
#             custs = data["customers"]

#             customer_lines = []

#             for c in custs:
#                 customer_lines.append(
#                     f"{c.full_name or '-'} ({c.phone or '-'}) | "
#                     f"User: {c.username or '-'} | "
#                     f"ISP: {c.isp.name if c.isp else '-'}"
#                 )

#             customer_text = ", ".join(customer_lines)

#             result = send_whatsapp_message(
#                 phone=phone,
#                 lco_name=lco_name,
#                 date_str=today_str,
#                 customer_list=customer_text
#             )

#             if result:
#                 self.stdout.write(
#                     self.style.SUCCESS(
#                         f"WhatsApp sent to {phone} | RESPONSE: {result}"
#                     )
#                 )
#             else:
#                 self.stderr.write(
#                     self.style.ERROR(
#                         f"Failed to send WhatsApp to {phone}"
#                     )
#                 )

#         self.stdout.write(
#             self.style.SUCCESS("WhatsApp alerts process completed")
#         )







from django.core.management.base import BaseCommand
from datetime import date
from pathlib import Path

from django.conf import settings

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet

from customers.utils import get_today_expiring_customers

from customers.management.commands.whatsapp import (
    send_whatsapp_message,
    send_whatsapp_document
)


class Command(BaseCommand):

    help = "Send WhatsApp expiry alerts with PDF report"

    def handle(self, *args, **kwargs):

        customers = get_today_expiring_customers()

        if not customers:
            self.stdout.write("No expiring customers today.")
            return

        today_str = date.today().strftime("%d %b %Y")

        lco_map = {}

        for customer in customers:

            if not customer.lco:
                continue

            phone = customer.lco.phone

            if not phone:
                continue

            phone = phone.replace("+", "").replace(" ", "")

            if not phone.startswith("91"):
                phone = f"91{phone}"

            if phone not in lco_map:

                lco_map[phone] = {
                    "lco_name": customer.lco.name,
                    "customers": []
                }

            lco_map[phone]["customers"].append(customer)

        for phone, data in lco_map.items():

            lco_name = data["lco_name"]
            custs = data["customers"]

            # ---------------------------------
            # Create PDF
            # ---------------------------------

            reports_dir = Path(settings.MEDIA_ROOT) / "expiry_reports"
            reports_dir.mkdir(parents=True, exist_ok=True)

            pdf_name = (
                f"expiry_{phone}_{date.today()}.pdf"
            )

            pdf_path = reports_dir / pdf_name

            doc = SimpleDocTemplate(str(pdf_path))

            styles = getSampleStyleSheet()

            content = []

            content.append(
                Paragraph(
                    f"Expiry Report - {today_str}",
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

                customer_text = f"""
                <b>{i}. {c.full_name or '-'}</b><br/>
                Phone: {c.phone or '-'}<br/>
                Username: {c.username or '-'}<br/>
                ISP: {c.isp.name if c.isp else '-'}<br/>
                """

                content.append(
                    Paragraph(
                        customer_text,
                        styles["BodyText"]
                    )
                )

                content.append(Spacer(1, 10))

            doc.build(content)

            # ---------------------------------
            # Send template
            # ---------------------------------

            template_result = send_whatsapp_message(
                phone=phone,
                lco_name=lco_name,
                date_str=today_str,
                customer_list=f"{len(custs)} customer(s) nearing expiry. Please see attached report."
            )

            print("TEMPLATE RESULT:")
            print(template_result)

            # ---------------------------------
            # Send PDF
            # ---------------------------------

            pdf_url = (
                f"{settings.SITE_URL}"
                f"{settings.MEDIA_URL}"
                f"expiry_reports/{pdf_name}"
            )
            print("\n===== PDF DEBUG =====")
            print("PDF PATH:", pdf_path)
            print("PDF EXISTS:", pdf_path.exists())
            print("PDF URL:", pdf_url)
            print("=====================\n")

            document_result = send_whatsapp_document(
                phone=phone,
                document_url=pdf_url,
                filename=pdf_name
            )

            print("DOCUMENT RESULT:")
            print(document_result)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Report sent to {phone}"
                )
            )