import requests

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

from customers.models import Customer


API_URL = f"{settings.SIGNAL_API_BASE_URL}/signals"


class Command(BaseCommand):
    help = "Fast sync ONU signals and ports"

    def handle(self, *args, **kwargs):

        try:
            print("1. Starting sync")

            response = requests.get(API_URL, timeout=30)

            print("2. API response received")

            response.raise_for_status()

            data = response.json()

            print(f"3. Records from API: {len(data)}")

            customer_map = {
                item["serial_number"]: {
                    "signal": item.get("rx_power"),
                    "port": item.get("port"),
                }
                for item in data
                if isinstance(item, dict)
                and item.get("serial_number")
            }

            print(
                f"4. Customer map created: {len(customer_map)}"
            )

            customers = Customer.objects.filter(
                ont_number__in=customer_map.keys()
            )

            print(
                f"5. Customers found in DB: {customers.count()}"
            )

            update_list = []

            # Single timestamp for entire sync
            sync_time = timezone.now()

            for customer in customers:

                api_data = customer_map.get(
                    customer.ont_number
                )

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

                # IMPORTANT:
                # auto_now does not work with bulk_update
                customer.last_updated = sync_time

                update_list.append(customer)

            print(
                f"6. Customers to update: {len(update_list)}"
            )

            batch_size = 1000

            for i in range(
                0,
                len(update_list),
                batch_size
            ):

                Customer.objects.bulk_update(
                    update_list[i:i + batch_size],
                    ["signal", "port", "last_updated"]
                )

                print(
                    f"Updated "
                    f"{min(i + batch_size, len(update_list))}"
                    f" of {len(update_list)}"
                )

            print("7. Bulk update completed")

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully updated "
                    f"{len(update_list)} customers"
                )
            )

        except Exception as e:

            self.stdout.write(
                self.style.ERROR(
                    f"Sync failed: {str(e)}"
                )
            )