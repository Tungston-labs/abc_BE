from django.core.management.base import BaseCommand
from datetime import date
from customers.utils import get_today_expiring_customers
from lcos.whatsapp import send_whatsapp_message


class Command(BaseCommand):
    help = "Send WhatsApp alerts for today's expiring customers"

    def handle(self, *args, **kwargs):
        customers = get_today_expiring_customers()

        # ✅ If no customers → stop cron quietly
        if not customers:
            self.stdout.write("No expiring customers today.")
            return

        # Format today's date → 09 Feb 2026
        today_str = date.today().strftime("%d %b %Y")

        lco_map = {}

        for c in customers:
            if c.lco and c.lco.phone:
                lco_map.setdefault(c.lco.phone, []).append(c)

        for phone, custs in lco_map.items():

            customer_list = ""
            for c in custs:
                customer_list += f"{c.full_name} ({c.phone})\n"

            try:
                send_whatsapp_message(
                    phone=phone,
                    lco_name="LCO",
                    date_str=today_str,
                    customer_list=customer_list
                )
                self.stdout.write(f"Sent to LCO: {phone}")
            except Exception as e:
                self.stderr.write(f"Failed for {phone}: {str(e)}")

        self.stdout.write(self.style.SUCCESS("WhatsApp alerts process completed"))
