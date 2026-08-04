import requests

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail

from customers.models import Customer, ServiceHealth
from customers.management.commands.whatsapp import send_signal_alert
from customers.management.commands.signal_health import mark_signal_recovered               

API_URL = f"{settings.SIGNAL_API_BASE_URL}/signals"





class Command(BaseCommand):
    help = "Fast sync ONU signals and ports"


    def mark_failed(self, subject, error):
        try:
            health, _ = ServiceHealth.objects.get_or_create(
                service="signal",
                defaults={"is_down": False},
            )

            if health.is_down:
                return

            health.is_down = True
            health.last_failure = timezone.now()
            health.last_error = str(error)
            health.save(update_fields=[
                "is_down",
                "last_failure",
                "last_error",
            ])

        except Exception as db_error:
            print(f"Could not update ServiceHealth: {db_error}")

        # Always try to send alerts, even if the database is unavailable.
        self.send_alert(subject, error)

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
            {timezone.localtime()}

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
                recipient_list=settings.SIGNAL_ALERT_EMAILS,
                fail_silently=False,
            )

            print("✅ Alert email sent successfully.")
            time_str = timezone.localtime().strftime("%d %b %Y %I:%M %p")

            for phone in settings.SIGNAL_ALERT_PHONES:
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

            if response.status_code != 200:

                try:
                    detail = response.json().get("detail", response.text)
                except Exception:
                    detail = response.text

                raise requests.exceptions.HTTPError(detail)

            data = response.json()

            print(f"3. Records from API: {len(data)}")

            customer_map = {
                item["serial_number"]: {
                    "signal": item.get("rx_power"),
                    "port": item.get("port"),
                    # "mac_id": item.get("mac_address"),
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
                # customer.mac_id = (
                #     api_data.get("mac_id").upper()
                #     if api_data.get("mac_id")
                #     else None
                # )

                customer.last_updated = sync_time

                update_list.append(customer)

            print(f"6. Customers to update: {len(update_list)}")

            batch_size = 1000

            for i in range(0, len(update_list), batch_size):

                Customer.objects.bulk_update(
                    update_list[i:i + batch_size],
                    [
                        "signal",
                        "port",
                        # "mac_id",
                        "last_updated",
                    ],
                )

                print(
                    f"Updated {min(i + batch_size, len(update_list))} "
                    f"of {len(update_list)}"
                )

            print("7. Bulk update completed")

            mark_signal_recovered()

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully updated {len(update_list)} customers"
                )
            )

        

        except requests.exceptions.ConnectionError as e:

            self.mark_failed(
                "🚨 Signal Server Unreachable",
                str(e)
            )

            self.stdout.write(
                self.style.ERROR(
                    f"Connection Error: {str(e)}"
                )
            )

        except requests.exceptions.Timeout as e:

            self.mark_failed(
                "🚨 Signal Server Timeout",
                str(e)
            )

            self.stdout.write(
                self.style.ERROR(
                    f"Timeout Error: {str(e)}"
                )
            )

        except requests.exceptions.HTTPError as e:

            self.mark_failed(
                "🚨 Signal API HTTP Error",
                str(e)
            )

            self.stdout.write(
                self.style.ERROR(
                    f"HTTP Error: {str(e)}"
                )
            )

        except Exception as e:

            self.mark_failed(
                "🚨 Signal Synchronization Failed",
                str(e)
            )

            self.stdout.write(
                self.style.ERROR(
                    f"Sync failed: {str(e)}"
                )
            )

        

        