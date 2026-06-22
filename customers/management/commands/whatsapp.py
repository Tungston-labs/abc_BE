# # lcos/whatsapp.py

# import json
# import logging
# from twilio.rest import Client
# from django.conf import settings

# logger = logging.getLogger(__name__)

# client = Client(
#     settings.TWILIO_ACCOUNT_SID,
#     settings.TWILIO_AUTH_TOKEN
# )


# def send_whatsapp_message(to_number, lco_name, date_str, customer_list):

#     try:
#         # clean phone
#         to_number = to_number.replace("+", "").replace(" ", "")

#         if not to_number.startswith("91"):
#             to_number = f"91{to_number}"

#         message = client.messages.create(
#             from_=settings.TWILIO_WHATSAPP_NUMBER,
#             to=f"whatsapp:+{to_number}",
#             content_sid=settings.TWILIO_TEMPLATE_SID,
#             content_variables=json.dumps({
#                 "1": lco_name,
#                 "2": date_str,
#                 "3": customer_list
#             })
#         )

#         return message.sid

#     except Exception as e:
#         logger.error(f"Twilio send failed for {to_number}: {str(e)}")
#         return None

# -----for meta whatspp-------

import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_whatsapp_message(phone, lco_name, date_str, customer_list):

    try:
        phone = phone.replace("+", "").replace(" ", "")

        url = (
            f"https://graph.facebook.com/"
            f"{settings.WHATSAPP_API_VERSION}/"
            f"{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        )

        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "template",
            "template": {
                "name": "alert_expiry",
                "language": {
                    "code": "en"
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": str(lco_name)
                            },
                            {
                                "type": "text",
                                "text": str(date_str)
                            },
                            {
                                "type": "text",
                                "text": str(customer_list)
                            }
                        ]
                    }
                ]
            }
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )

        logger.info("WhatsApp Status: %s", response.status_code)
        logger.info("WhatsApp Response: %s", response.text)

        if response.status_code in [200, 201]:
            return response.json()

        logger.error("WhatsApp Error: %s", response.text)
        return None

    except Exception as e:
        logger.exception("WhatsApp send error")
        return None