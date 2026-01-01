from twilio.rest import Client
from django.conf import settings

def send_whatsapp_message(to_number, message_text):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    try:
        message = client.messages.create(
            from_=settings.TWILIO_WHATSAPP_NUMBER,
            to=f"whatsapp:{to_number}",
            body=message_text
        )
        return message.sid
    except Exception as e:
        print("WhatsApp sending failed:", e)
        return None
