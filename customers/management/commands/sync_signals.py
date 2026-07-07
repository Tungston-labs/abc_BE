import requests

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail

from customers.models import Customer
from customers.management.commands.whatsapp import send_signal_alert

API_URL = f"{settings.SIGNAL_API_BASE_URL}/signals"

ADMIN_EMAILS = [
    "aluvabroadband@gmail.com",
    "nisna.u5@gmail.com",
]
ADMIN_PHONES = [
    "919400148247",
    "917025220037",
    "919746467290"
]


class Command(BaseCommand):
    help = "Fast sync ONU signals and ports"

    def send_alert(self, subject, error):
        """
        Send email alert to administrators.
        """
        try:
            send_mail(
                subject=subject,
                message=f"""
            Hello Admin,

            The Signal Synchronization process has failed.

            Time:
            {timezone.now()}

            API:
            {API_URL}

            Reason:
            {error}

            Please check:

            • Remote Signal Server
            • FastAPI Service
            • Network Connectivity
            • Server Status

            This is an automated notification from ABC CRM.
            """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=ADMIN_EMAILS,
                fail_silently=False,
            )

            print("✅ Alert email sent successfully.")
            time_str = timezone.localtime().strftime("%d %b %Y %I:%M %p")

            for phone in ADMIN_PHONES:
                try:
                    send_signal_alert(
                        phone=phone,
                        service="Signal Synchronization",
                        status="Failed",
                        time_str=time_str,
                        reason=str(error),
                    )
                    print(f"✅ WhatsApp alert sent to {phone}")

                except Exception as whatsapp_error:
                    print(f"❌ WhatsApp failed for {phone}: {whatsapp_error}")

        except Exception as mail_error:
            print(f"❌ Failed to send alert email: {mail_error}")

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

            print(f"4. Customer map created: {len(customer_map)}")

            customers = Customer.objects.filter(
                ont_number__in=customer_map.keys()
            )

            print(f"5. Customers found in DB: {customers.count()}")

            update_list = []

            sync_time = timezone.now()

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

                customer.last_updated = sync_time

                update_list.append(customer)

            print(f"6. Customers to update: {len(update_list)}")

            batch_size = 1000

            for i in range(0, len(update_list), batch_size):

                Customer.objects.bulk_update(
                    update_list[i:i + batch_size],
                    ["signal", "port", "last_updated"],
                )

                print(
                    f"Updated {min(i + batch_size, len(update_list))} "
                    f"of {len(update_list)}"
                )

            print("7. Bulk update completed")

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully updated {len(update_list)} customers"
                )
            )

        except requests.exceptions.ConnectionError as e:

            self.send_alert(
                "🚨 Signal Server Unreachable",
                str(e)
            )

            self.stdout.write(
                self.style.ERROR(
                    f"Connection Error: {str(e)}"
                )
            )

        except requests.exceptions.Timeout as e:

            self.send_alert(
                "🚨 Signal Server Timeout",
                str(e)
            )

            self.stdout.write(
                self.style.ERROR(
                    f"Timeout Error: {str(e)}"
                )
            )

        except requests.exceptions.HTTPError as e:

            self.send_alert(
                "🚨 Signal API HTTP Error",
                str(e)
            )

            self.stdout.write(
                self.style.ERROR(
                    f"HTTP Error: {str(e)}"
                )
            )

        except Exception as e:

            self.send_alert(
                "🚨 Signal Synchronization Failed",
                str(e)
            )

            self.stdout.write(
                self.style.ERROR(
                    f"Sync failed: {str(e)}"
                )
            )