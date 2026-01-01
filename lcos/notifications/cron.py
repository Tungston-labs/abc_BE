from datetime import date, timedelta
from customers.models import Customer
from notifications.whatsapp import send_whatsapp_message

def send_expiry_alerts():
    today = date.today()
    next_week = today + timedelta(days=7)

    customers = Customer.objects.filter(
        expiry_date__range=[today, next_week],
        lco__isnull=False
    )

    lco_map = {}

    for customer in customers:
        lco = customer.lco

        if lco.phone not in lco_map:
            lco_map[lco.phone] = []

        lco_map[lco.phone].append(customer)

    for phone, cust_list in lco_map.items():
        msg = "⚠️ *Upcoming Expiry Alerts*\n\n"
        
        for c in cust_list:
            msg += f"• {c.full_name} — Expiring on {c.expiry_date}\n"

        msg += "\nPlease follow up accordingly."

        send_whatsapp_message(phone, msg)

        print(f"WhatsApp sent to LCO {phone}")
