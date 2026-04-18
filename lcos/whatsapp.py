# # services/whatsapp.py
# from twilio.rest import Client
# from django.conf import settings

# def send_whatsapp_message(to_number, message_text):
#     client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

#     message = client.messages.create(
#         body=message_text,
#         from_=settings.TWILIO_WHATSAPP_NUMBER,
#         to=f"whatsapp:{to_number}",
#     )

#     return message.sid
import requests
from django.conf import settings

def send_whatsapp_message(phone, lco_name, date_str, customer_list):
    url = f"https://graph.facebook.com/v19.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
    "messaging_product": "whatsapp",
    "to": phone,
    "type": "template",
    "template": {
        "name": "hello_world",
        "language": {"code": "en_US"}
    }
}

    response = requests.post(url, json=data, headers=headers)

    print("STATUS:", response.status_code)
    print("RESPONSE:", response.text)

    return response.json()