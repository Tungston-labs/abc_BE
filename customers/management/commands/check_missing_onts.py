import requests

from django.core.management.base import BaseCommand
from django.conf import settings

from customers.models import Customer


API_URL = f"{settings.SIGNAL_API_BASE_URL}/signals"


class Command(BaseCommand):
    help = "Check MIB ONTs from Signal API that are missing in Customer database"

    def handle(self, *args, **kwargs):

        try:
            self.stdout.write("Starting MIB ONT check...")
            self.stdout.write(f"Fetching data from: {API_URL}")

            # ----------------------------------------
            # 1. Call Signal API
            # ----------------------------------------
            response = requests.get(
                API_URL,
                timeout=30
            )

            response.raise_for_status()

            data = response.json()

            self.stdout.write(
                f"Signal API returned {len(data)} records"
            )

            # ----------------------------------------
            # 2. Extract serial numbers from API
            # ----------------------------------------
            api_serials = {
                str(item.get("serial_number")).strip()
                for item in data
                if isinstance(item, dict)
                and item.get("serial_number")
            }

            self.stdout.write(
                f"Unique MIB serial numbers: {len(api_serials)}"
            )

            # ----------------------------------------
            # 3. Get ONT numbers from Customer DB
            # ----------------------------------------
            customer_serials = set(
                Customer.objects
                .exclude(ont_number__isnull=True)
                .exclude(ont_number="")
                .values_list("ont_number", flat=True)
            )

            customer_serials = {
                str(serial).strip()
                for serial in customer_serials
                if serial
            }

            self.stdout.write(
                f"Customer ONT numbers in Django: "
                f"{len(customer_serials)}"
            )

            # ----------------------------------------
            # 4. Find MIB serials missing in Django
            # ----------------------------------------
            missing_serials = sorted(
                api_serials - customer_serials
            )

            # ----------------------------------------
            # 5. Print result
            # ----------------------------------------
            self.stdout.write("")
            self.stdout.write("=" * 60)
            self.stdout.write("MIB ONT CHECK RESULT")
            self.stdout.write("=" * 60)

            self.stdout.write(
                f"Total MIB serials : {len(api_serials)}"
            )

            self.stdout.write(
                f"Found in Django   : "
                f"{len(api_serials & customer_serials)}"
            )

            self.stdout.write(
                f"Missing in Django : {len(missing_serials)}"
            )

            self.stdout.write("=" * 60)

            if missing_serials:

                self.stdout.write("")
                self.stdout.write(
                    "❌ MIB ONTs NOT FOUND IN CUSTOMER TABLE:"
                )
                self.stdout.write("-" * 60)

                for serial in missing_serials:
                    self.stdout.write(serial)

                self.stdout.write("-" * 60)

            else:

                self.stdout.write("")
                self.stdout.write(
                    "✅ All MIB ONTs are present in Django."
                )

            self.stdout.write("")
            self.stdout.write("MIB ONT check completed.")

        except requests.exceptions.ConnectionError as e:

            self.stderr.write(
                f"❌ Could not connect to Signal API: {e}"
            )

        except requests.exceptions.Timeout as e:

            self.stderr.write(
                f"❌ Signal API timeout: {e}"
            )

        except requests.exceptions.HTTPError as e:

            self.stderr.write(
                f"❌ Signal API HTTP error: {e}"
            )

        except Exception as e:

            self.stderr.write(
                f"❌ Error: {e}"
            )
