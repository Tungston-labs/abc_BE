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
            "name": "expiry_alert",
            "language": {"code": "en"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": lco_name},
                        {"type": "text", "text": date_str},
                        {"type": "text", "text": customer_list}
                    ]
                }
            ]
        }
    }

    response = requests.post(url, json=data, headers=headers)
    return response.json()