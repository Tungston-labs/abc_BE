from datetime import date, timedelta
from .models import Customer


def get_today_expiring_customers():
    from_date = date.today()
    to_date = from_date + timedelta(days=5)

    customers = Customer.objects.filter(
        expiry_date__range=(from_date, to_date)
    ).select_related("lco")

    return customers