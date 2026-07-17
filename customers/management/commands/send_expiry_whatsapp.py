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

