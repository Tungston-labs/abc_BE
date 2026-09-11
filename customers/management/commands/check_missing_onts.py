
import requests

from django.core.management.base import BaseCommand
from django.conf import settings

from customers.models import Customer


API_URL = f"{settings.SIGNAL_API_BASE_URL}/signals"


class Command(BaseCommand):
    help = "List MIB ONTs that are missing from Django Customer database"


class Command(BaseCommand):
    help = "List MIB ONTs missing from Django Customer database"

    def handle(self, *args, **kwargs):

        try:
            # ========================================
            # 1. Fetch Signal API
            # ========================================

            self.stdout.write("Starting MIB ONT check...")
            self.stdout.write(f"Fetching: {API_URL}")

            response = requests.get(
                API_URL,
                timeout=30
            )

            response.raise_for_status()

            data = response.json()

            self.stdout.write(
                f"Signal API records: {len(data)}"
            )

            # ========================================
            # 2. Get all MIB serial numbers
            # ========================================

            api_serials = {
                str(item.get("serial_number")).strip()
                for item in data
                if isinstance(item, dict)
                and item.get("serial_number")
            }

            self.stdout.write(
                f"Unique MIB ONTs: {len(api_serials)}"
            )

            # ========================================
            # 3. Get Customer ONT numbers
            # ========================================

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
                f"Customer ONTs: {len(customer_serials)}"
            )

            # ========================================
            # 4. Find missing serial numbers
            # ========================================

            missing_serials = api_serials - customer_serials

            # ========================================
            # 5. Get complete API records
            #    for missing ONTs
            # ========================================

            missing_onts = [
                item
                for item in data
                if isinstance(item, dict)
                and item.get("serial_number")
                and str(item.get("serial_number")).strip()
                in missing_serials
            ]

            # ========================================
            # 6. Print summary
            # ========================================

            self.stdout.write("")
            self.stdout.write("=" * 80)
            self.stdout.write("MIB ONT CHECK RESULT")
            self.stdout.write("=" * 80)

            self.stdout.write(
                f"Total MIB ONTs       : {len(api_serials)}"
            )

            self.stdout.write(
                f"Found in Django      : "
                f"{len(api_serials & customer_serials)}"
            )

            self.stdout.write(
                f"Missing in Django    : {len(missing_onts)}"
            )

            self.stdout.write("=" * 80)

            # ========================================
            # 7. Print complete details
            # ========================================

            if missing_onts:

                self.stdout.write("")
                self.stdout.write(
                    "❌ MIB ONTs NOT FOUND IN CUSTOMER TABLE"
                )
                self.stdout.write("=" * 80)

                for index, item in enumerate(
                    missing_onts,
                    start=1
                ):

                    self.stdout.write("")
                    self.stdout.write(
                        f"--------------- ONT #{index} ---------------"
                    )

                    self.stdout.write(
                        f"ONT Number : "
                        f"{item.get('serial_number', '-')}"
                    )

                    self.stdout.write(
                        f"OLT        : "
                        f"{item.get('olt', item.get('olt_ip', '-'))}"
                    )

                    self.stdout.write(
                        f"MAC        : "
                        f"{item.get('mac_address', item.get('mac', '-'))}"
                    )

                    self.stdout.write(
                        f"Port       : "
                        f"{item.get('port', '-')}"
                    )

                    self.stdout.write(
                        f"RX Power   : "
                        f"{item.get('rx_power', '-')}"
                    )

                    self.stdout.write(
                        f"TX Power   : "
                        f"{item.get('tx_power', '-')}"
                    )

                    self.stdout.write(
                        f"Status     : "
                        f"{item.get('status', '-')}"
                    )

                    # Print any additional fields returned
                    # by the Signal API.
                    self.stdout.write(
                        "----------------------------------------"
                    )

                self.stdout.write("")
                self.stdout.write("=" * 80)

            else:

                self.stdout.write("")
                self.stdout.write(
                    "✅ All MIB ONTs are present in Django."
                )

            self.stdout.write("")
            self.stdout.write(
                "MIB ONT check completed."
            )

        except requests.exceptions.ConnectionError as e:

            self.stderr.write(
                f"❌ Signal API connection error: {e}"
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

