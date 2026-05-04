# # lcos/whatsapp.py

import json
import logging
from twilio.rest import Client
from django.conf import settings

logger = logging.getLogger(__name__)

client = Client(
    settings.TWILIO_ACCOUNT_SID,
    settings.TWILIO_AUTH_TOKEN
)


def send_whatsapp_message(to_number, lco_name, date_str, customer_list):

    try:
        # clean phone
        to_number = to_number.replace("+", "").replace(" ", "")

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

    except Exception as e:
        logger.error(f"Twilio send failed for {to_number}: {str(e)}")
        return None

# -----for meta whatspp-------



# import requests
# import logging
# from django.conf import settings

# logger = logging.getLogger(__name__)


# def send_whatsapp_message(phone, lco_name, date_str, customer_list):

#     try:
#         # clean phone (must be international format WITHOUT +)
#         phone = phone.replace("+", "").replace(" ", "")

#         url = f"https://graph.facebook.com/v19.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"

#         headers = {
#             "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
#             "Content-Type": "application/json"
#         }

#         data = {
#             "messaging_product": "whatsapp",
#             "to": phone,
#             "type": "template",
#             "template": {
#                 "name": "alert_expiry",
#                 "language": {"code": "en"},
#                 "components": [
#                     {
#                         "type": "body",
#                         "parameters": [
#                             {"type": "text", "text": lco_name},
#                             {"type": "text", "text": date_str},
#                             {"type": "text", "text": customer_list}
#                         ]
#                     }
#                 ]
#             }
#         }

#         response = requests.post(url, json=data, headers=headers)

#         logger.info(f"WhatsApp STATUS: {response.status_code}")
#         logger.info(f"WhatsApp RESPONSE: {response.text}")

#         if response.status_code == 200:
#             return response.json()
#         else:
#             return None

#     except Exception as e:
#         logger.error(f"WhatsApp send error: {str(e)}")
#         return None