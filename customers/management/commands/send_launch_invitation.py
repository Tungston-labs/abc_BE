from django.core.management.base import BaseCommand

from customers.models import LCO
from customers.management.commands.whatsapp import (
    send_expiry_customer_chunk,
)


class Command(BaseCommand):

    help = "Send software launch invitation to all operators"

    def handle(self, *args, **kwargs):

        operators = (
            LCO.objects
            .exclude(phone__isnull=True)
            .exclude(phone__exact="")
        )

        message = (
            "Dear Operators, you are cordially invited to the official launch "
            "of our new software. Join us on June 30th at 10:00 AM at Hotel "
            "Periyar, Aluva. Your presence would mean a lot to us. "
            "See you there!"
        )

        for operator in operators:

            phone = (
                operator.phone
                .replace("+", "")
                .replace(" ", "")
                .replace("-", "")
            )

            if not phone.startswith("91"):
                phone = f"91{phone}"

            print(f"Sending to {operator.name} ({phone})")

            result = send_expiry_customer_chunk(
                phone=phone,
                customer_text=message
            )

            if result:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Invitation sent to {operator.name}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed: {operator.name}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Invitation process completed."
            )
        )