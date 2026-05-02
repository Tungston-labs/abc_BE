import requests
from django.core.management.base import BaseCommand
from customers.models import Customer
from django.conf import settings
API_URL = settings.SIGNAL_API_BASE_URL

class Command(BaseCommand):
    help = "Fast sync ONU signals"

    def handle(self, *args, **kwargs):

        response = requests.get(API_URL, timeout=30)
        data = response.json()

        # STEP 1: create lookup map from API
        signal_map = {
            item["serial_number"]: item["rx_power"]
            for item in data if item.get("serial_number")
        }

        # STEP 2: fetch all matching customers in ONE query
        customers = Customer.objects.filter(
            ont_number__in=signal_map.keys()
        )

        update_list = []

        for customer in customers:
            customer.signal = signal_map.get(customer.ont_number)
            update_list.append(customer)

        # STEP 3: bulk update (VERY FAST)
        Customer.objects.bulk_update(update_list, ["signal", "last_updated"])

        self.stdout.write(
            self.style.SUCCESS(f"Updated {len(update_list)} customers")
        )