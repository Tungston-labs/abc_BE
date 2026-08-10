from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from zoneinfo import ZoneInfo

from customers.models import ServiceHealth
from customers.management.commands.whatsapp import send_signal_recovered


def mark_signal_recovered():

    try:
        health, _ = ServiceHealth.objects.get_or_create(
            service="signal",
            defaults={"is_down": False},
        )

        # Already UP → nothing to do
        if not health.is_down:
            print("ℹ️ Signal already UP. No recovery alert.")
            return

        # DOWN → UP
        health.is_down = False
        health.last_recovery = timezone.now()
        health.last_error = ""

        health.save(
            update_fields=[
                "is_down",
                "last_recovery",
                "last_error",
            ]
        )

        print("✅ Signal changed: DOWN → UP")

    except Exception as db_error:
        print(
            f"❌ Could not update ServiceHealth during recovery: "
            f"{db_error}"
        )
        return

    # =========================
    # RECOVERY EMAIL
    # =========================

    try:
        send_mail(
            subject="✅ Signal Server Recovered",
            message=f"""
Hello Admin,

Signal Synchronization has resumed successfully.

Time:
{timezone.localtime()}

The Signal Server is reachable again.

This is an automated notification from ABC CRM.
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=settings.SIGNAL_ALERT_EMAILS,
            fail_silently=False,
        )

        print("✅ Recovery email sent successfully.")

    except Exception as email_error:
        print(
            f"❌ Recovery email failed: {email_error}"
        )

    # =========================
    # RECOVERY WHATSAPP
    # =========================

    time_str = (
        timezone.now()
        .astimezone(ZoneInfo("Asia/Kolkata"))
        .strftime("%d %b %Y %I:%M %p")
    )

    for phone in settings.SIGNAL_ALERT_PHONES:

        try:
            result = send_signal_recovered(
                phone=phone,
                service="Signal Synchronization",
                status="Recovered",
                time_str=time_str,
            )

            if result:
                print(
                    f"✅ Recovery WhatsApp sent to {phone}"
                )
            else:
                print(
                    f"❌ Recovery WhatsApp rejected for {phone}"
                )

        except Exception as whatsapp_error:
            print(
                f"❌ Recovery WhatsApp error for "
                f"{phone}: {whatsapp_error}"
            )