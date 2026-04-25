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

        lco_map = {}

        for c in customers:
            if c.lco and c.lco.phone:
                lco_map.setdefault(c.lco.phone, []).append(c)

        for phone, custs in lco_map.items():

            # ✅ Remove +
            phone = phone.replace("+", "")

            # ✅ NO newline (IMPORTANT)
            customer_list = ", ".join([
            f"{c.full_name or c.username or '-'} "
            f"({c.phone or '-'}) "
            f"| User: {c.username or '-'} "
            f"| ISP: {c.isp.name if c.isp else '-'}"
            for c in custs
        ])

            try:
                result = send_whatsapp_message(
                    phone=phone,
                    lco_name="LCO",
                    date_str=today_str,
                    customer_list=customer_list
                )

                print("META RESPONSE:", result)
                self.stdout.write(f"Sent to LCO: {phone}")

            except Exception as e:
                self.stderr.write(f"Failed for {phone}: {str(e)}")

        self.stdout.write(self.style.SUCCESS("WhatsApp alerts process completed"))