# # customers/management/commands/send_expiry_whatsapp.py

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

        # group by LCO
        lco_map = {}

        for customer in customers:

            if customer.lco and customer.lco.phone:

                phone = customer.lco.phone.replace("+", "").replace(" ", "")

                if phone not in lco_map:
                    lco_map[phone] = {
                        "lco_name": customer.lco.name if customer.lco.name else "LCO",
                        "customers": []
                    }

                lco_map[phone]["customers"].append(customer)

        # send messages per LCO
        for phone, data in lco_map.items():

            lco_name = data["lco_name"]
            custs = data["customers"]

            customer_lines = []

            for c in custs:
                line = (
                    f"{c.full_name or '-'} "
                    f"({c.phone or '-'}) "
                    f"| User: {c.username or '-'} "
                    f"| ISP: {c.isp.name if c.isp else '-'}"
                )
                customer_lines.append(line)

            # keep message safe for WhatsApp template
            customer_text = ", ".join(customer_lines)

            sid = send_whatsapp_message(
                to_number=phone,
                lco_name=lco_name,
                date_str=today_str,
                customer_list=customer_text
            )

            if sid:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"WhatsApp sent to {phone} | SID: {sid}"
                    )
                )
            else:
                self.stderr.write(
                    self.style.ERROR(
                        f"Failed to send WhatsApp to {phone}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                "WhatsApp alerts process completed"
            )
        )




# # ----whtspp meta


# from django.core.management.base import BaseCommand
# from datetime import date

# from customers.utils import get_today_expiring_customers
# from lcos.whatsapp import send_whatsapp_message


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