# customers/management/commands/send_expiry_whatsapp.py

from django.core.management.base import BaseCommand
from datetime import date

from customers.utils import get_today_expiring_customers
from lcos.whatsapp import send_whatsapp_message


class Command(BaseCommand):

    help = "Send WhatsApp alerts for today's expiring customers"

    def handle(self, *args, **kwargs):

        customers = get_today_expiring_customers()

        if not customers:
            self.stdout.write("No expiring customers today.")
            return

        today_str = date.today().strftime("%d %b %Y")

        # group customers by LCO phone
        lco_map = {}

        for customer in customers:

            if customer.lco and customer.lco.phone:

                phone = (
                    customer.lco.phone
                    .replace("+", "")
                    .replace(" ", "")
                )

                if phone not in lco_map:
                    lco_map[phone] = []

                lco_map[phone].append(customer)

        # send one WhatsApp per LCO
        for phone, custs in lco_map.items():

            customer_lines = []

            for c in custs:

                line = (
                    f"{c.full_name or '-'} "
                    f"({c.phone or '-'}) "
                    f"| User: {c.username or '-'} "
                    f"| ISP: {c.isp.name if c.isp else '-'}"
                )

                customer_lines.append(line)

            # IMPORTANT:
            # avoid newline in template variables
            customer_text = ", ".join(customer_lines)

            try:

                sid = send_whatsapp_message(
                    to_number=phone,
                    lco_name="LCO",
                    date_str=today_str,
                    customer_list=customer_text
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"WhatsApp sent to {phone} | SID: {sid}"
                    )
                )

            except Exception as e:

                self.stderr.write(
                    self.style.ERROR(
                        f"Failed for {phone}: {str(e)}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                "WhatsApp alerts process completed"
            )
        )