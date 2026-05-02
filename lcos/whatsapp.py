# lcos/whatsapp.py

import json

from twilio.rest import Client
from django.conf import settings


client = Client(
    settings.TWILIO_ACCOUNT_SID,
    settings.TWILIO_AUTH_TOKEN
)


def send_whatsapp_message(
    to_number,
    lco_name,
    date_str,
    customer_list
):

    # clean phone
    to_number = (
        to_number
        .replace("+", "")
        .replace(" ", "")
    )

    if not to_number.startswith("91"):
        to_number = f"91{to_number}"

    message = client.messages.create(

    from_=settings.TWILIO_WHATSAPP_NUMBER,

    to=f"whatsapp:+{to_number}",

    content_sid=settings.TWILIO_TEMPLATE_SID,

    content_variables=json.dumps({
        "1": lco_name,
        "2": date_str,
        "3": customer_list
    })
)

    return message.sid

# -----for meta whatspp-------



# import requests
# from django.conf import settings

# def send_whatsapp_message(phone, lco_name, date_str, customer_list):
#     url = f"https://graph.facebook.com/v19.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"

#     headers = {
#         "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
#         "Content-Type": "application/json"
#     }

#     data = {
#         "messaging_product": "whatsapp",
#         "to": phone,
#         "type": "template",
#         "template": {
#             "name": "alert_expiry",
#             "language": {"code": "en"},
#             "components": [
#                 {
#                     "type": "body",
#                     "parameters": [
#                         {"type": "text", "text": lco_name},
#                         {"type": "text", "text": date_str},
#                         {"type": "text", "text": customer_list}
#                     ]
#                 }
#             ]
#         }
#     }

#     response = requests.post(url, json=data, headers=headers)

#     print("STATUS:", response.status_code)
#     print("RESPONSE:", response.text)

#     return response.json()