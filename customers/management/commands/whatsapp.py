

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
    





    # for ticket notification

def send_ticket_update_whatsapp(
    phone,
    lco_name,
    ticket_id,
    ticket_type,
    status,
    admin_reply
):

    phone = phone.replace("+", "").replace(" ", "")

    url = f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "template",
        "template": {
            "name": "ticket_status_update",
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
                            "text": str(ticket_type)
                        },
                        {
                            "type": "text",
                            "text": str(status)
                        },
                        {
                            "type": "text",
                            "text": str(ticket_id)
                        },
                        {
                            "type": "text",
                            "text": str(admin_reply)
                        }
                    ]
                }
            ]
        }
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload
    )

    return response.json()