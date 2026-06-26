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
    

    # extra messages with tepmlates


def send_expiry_customer_chunk(
    phone,
    customer_text
):

    phone = (
        str(phone)
        .replace("+", "")
        .replace(" ", "")
        .replace("-", "")
    )

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
            "name": "expiry_customers",
            "language": {
                "code": "en"
            },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": customer_text
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

    print("\n===== CUSTOMER TEMPLATE =====")
    print("STATUS:", response.status_code)
    print("RESPONSE:", response.text)
    print("=============================\n")

    if response.status_code in (200, 201):
        return response.json()

    return None




# extra message-------   
# def send_whatsapp_text(phone, message):

#     phone = (
#         str(phone)
#         .replace("+", "")
#         .replace(" ", "")
#         .replace("-", "")
#     )

#     url = (
#         f"https://graph.facebook.com/"
#         f"{settings.WHATSAPP_API_VERSION}/"
#         f"{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
#     )

#     headers = {
#         "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
#         "Content-Type": "application/json",
#     }

#     payload = {
#         "messaging_product": "whatsapp",
#         "to": phone,
#         "type": "text",
#         "text": {
#             "preview_url": False,
#             "body": message
#         }
#     }

#     response = requests.post(
#         url,
#         headers=headers,
#         json=payload,
#         timeout=30
#     )

#     print("\n===== TEXT RESPONSE =====")
#     print(response.status_code)
#     print(response.text)
#     print("=========================\n")

#     return response.json()









# -----document sending through whatspp-----
# import requests
# from django.conf import settings

# def send_whatsapp_document(
#     phone,
#     document_url,
#     filename="Expiry_Report.pdf"
# ):

#     phone = (
#         str(phone)
#         .replace("+", "")
#         .replace(" ", "")
#         .replace("-", "")
#     )

#     url = (
#         f"https://graph.facebook.com/"
#         f"{settings.WHATSAPP_API_VERSION}/"
#         f"{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
#     )

#     headers = {
#         "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
#         "Content-Type": "application/json",
#     }

#     payload = {
#         "messaging_product": "whatsapp",
#         "recipient_type": "individual",
#         "to": phone,
#         "type": "document",
#         "document": {
#             "link": document_url,
#             "filename": filename,
#             "caption": "Expiry Customer Report"
#         }
#     }

#     print("\n===== DOCUMENT REQUEST =====")
#     print(payload)
#     print("============================\n")

#     response = requests.post(
#         url,
#         headers=headers,
#         json=payload,
#         timeout=60
#     )

#     print("\n===== DOCUMENT RESPONSE =====")
#     print("STATUS:", response.status_code)
#     print("RESPONSE:", response.text)
#     print("=============================\n")

#     try:
#         return response.json()
#     except Exception:
#         return response.text
# --------------ticket notifications-------


import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_ticket_update_whatsapp(
    phone,
    lco_name,
    ticket_id,
    ticket_type,
    status,
    admin_reply
):
    try:

        phone = (
            str(phone)
            .replace("+", "")
            .replace(" ", "")
            .replace("-", "")
        )

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
            json=payload,
            timeout=30
        )

        print("\n===== WHATSAPP TICKET RESPONSE =====")
        print("PHONE:", phone)
        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text)
        print("===================================\n")

        logger.info(response.text)

        if response.status_code in [200, 201]:
            return response.json()

        return None

    except Exception as e:

        print("\n===== WHATSAPP ERROR =====")
        print(str(e))
        print("==========================\n")

        logger.exception("Ticket WhatsApp Error")

        return None