# services/whatsapp.py
from twilio.rest import Client
from django.conf import settings

def send_whatsapp_message(to_number, message_text):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    message = client.messages.create(
        body=message_text,
        from_=settings.TWILIO_WHATSAPP_NUMBER,
        to=f"whatsapp:{to_number}",
    )

    return message.sid
