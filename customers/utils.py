from datetime import date
from .models import Customer

def get_today_expiring_customers():
    today = date.today()
    return Customer.objects.filter(expiry_date=today).select_related("lco")
