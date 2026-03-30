import requests
from datetime import datetime, timedelta


def fetch_stampede_data(mapping):
    isp = mapping.isp

    token = isp.token  # ✅ static for now

    today = datetime.now()

    from_date = (today - timedelta(days=20)).strftime("%Y-%m-%d %H:%M:%S")
    to_date = (today + timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "partnerName": mapping.partner_name,
        "expiryFrom": from_date,
        "expiryTill": to_date
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        "https://api.stampede.com/endpoint",  # replace
        json=payload,
        headers=headers
    )

    return response.json()