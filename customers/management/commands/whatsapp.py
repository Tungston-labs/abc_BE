import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


# ----------------------------------------------------
# FIRST TEMPLATE
# ----------------------------------------------------

def send_whatsapp_message(phone, lco_name, date_str, customer_list):

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

        print("\n===== FIRST TEMPLATE PAYLOAD =====")
        print(payload)
        print("==================================\n")

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )

        print("\n===== FIRST TEMPLATE RESPONSE =====")
        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text)
        print("===================================\n")

        if response.status_code in (200, 201):
            return response.json()

        return None

    except Exception as e:
        logger.exception(e)
        return None


# ----------------------------------------------------
# CUSTOMER CHUNK TEMPLATE
# ----------------------------------------------------

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
            "name": "alert_expiry_customers",
            "language": {
                "code": "en"
            },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": str(customer_text)
                        }
                    ]
                }
            ]
        }
    }

    print("\n========== CUSTOMER TEXT ==========")
    print(customer_text)
    print("===================================\n")

    print("\n========== TEMPLATE PAYLOAD ==========")
    print(payload)
    print("======================================\n")

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=30
    )

    print("\n===== CUSTOMER TEMPLATE RESPONSE =====")
    print("STATUS :", response.status_code)
    print("RESPONSE :", response.text)
    print("======================================\n")

    try:
        data = response.json()
    except Exception:
        data = response.text

    return data if response.status_code in (200, 201) else None




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
        print("lco_name:", lco_name)
        print("ticket_type:", ticket_type)
        print("status:", status)
        print("ticket_id:", ticket_id)
        print("admin_reply:", admin_reply)

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
    
# remote server signal alert

def send_signal_alert(phone, service, status, time_str, reason):

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
            "name": "signal_sync_alert",
            "language": {
                "code": "en"
            },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": service
                        },
                        {
                            "type": "text",
                            "text": status
                        },
                        {
                            "type": "text",
                            "text": time_str
                        },
                        {
                            "type": "text",
                            "text": reason
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

    print(response.status_code)
    print(response.text)

    return response.json()


def send_signal_recovered(phone, service, status, time_str):

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
            "name": "signal_server_recovered",
            "language": {
                "code": "en"
            },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": service
                        },
                        {
                            "type": "text",
                            "text": status
                        },
                        {
                            "type": "text",
                            "text": time_str
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
        timeout=30,
    )

    print("\n===== SIGNAL RECOVERED RESPONSE =====")
    print(response.status_code)
    print(response.text)
    print("=====================================\n")

    return response.json()
