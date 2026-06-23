import requests
from django.core.management.base import BaseCommand
from customers.models import Customer
from django.conf import settings

API_URL = f"{settings.SIGNAL_API_BASE_URL}/signals"


class Command(BaseCommand):
    help = "Fast sync ONU signals and ports"

    def handle(self, *args, **kwargs):

        response = requests.get(API_URL, timeout=30)

        response.raise_for_status()

        data = response.json()

        customer_map = {
            item["serial_number"]: {
                "signal": item.get("rx_power"),
                "port": item.get("port"),
            }
            for item in data
            if isinstance(item, dict) and item.get("serial_number")
        }

        customers = Customer.objects.filter(
            ont_number__in=customer_map.keys()
        )

        update_list = []

        for customer in customers:
            api_data = customer_map.get(customer.ont_number)

            customer.signal = (
                str(api_data.get("signal"))
                if api_data.get("signal") is not None
                else None
            )

            customer.port = (
                str(api_data.get("port"))
                if api_data.get("port") is not None
                else None
            )

            update_list.append(customer)

        Customer.objects.bulk_update(
            update_list,
            ["signal", "port", "last_updated"]
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Updated {len(update_list)} customers"
            )
        )