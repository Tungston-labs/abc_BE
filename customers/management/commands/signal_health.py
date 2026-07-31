from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from zoneinfo import ZoneInfo


from customers.models import ServiceHealth
from customers.management.commands.whatsapp import send_signal_alert


def mark_signal_recovered():
    """
    Send recovery notification only once.
    """

    health, _ = ServiceHealth.objects.get_or_create(
        service="signal",
        defaults={"is_down": False},
    )

    if not health.is_down:
        return

    try:
        send_mail(
            subject="✅ Signal Server Recovered",
            message=f"""
Hello Admin,

Signal Synchronization has resumed successfully.

Time:
{timezone.now()}

The Signal Server is reachable again.

This is an automated notification from ABC CRM.
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=settings.SIGNAL_ALERT_EMAILS,
            fail_silently=False,
        )
    except Exception as e:
        print(f"Email Error: {e}")


    time_str = (
        timezone.now()
        .astimezone(ZoneInfo("Asia/Kolkata"))
        .strftime("%d %b %Y %I:%M %p")
    )

    for phone in settings.SIGNAL_ALERT_PHONES:
        try:
            send_signal_alert(
                phone=phone,
                service="Signal Synchronization",
                status="Recovered",
                time_str=time_str,
                reason="Server reachable again",
            )
        except Exception as e:
            print(f"WhatsApp Error ({phone}): {e}")

    health.is_down = False
    health.last_recovery = timezone.now()
    health.last_error = ""
    health.save()