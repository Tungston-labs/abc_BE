import requests
from datetime import datetime, timedelta


def fetch_stampede_data(mapping):
    isp = mapping.isp

    token = isp.token  # static token for now

    today = datetime.now()

    from_date = (today - timedelta(days=100)).strftime("%Y-%m-%d %H:%M:%S")
    to_date = (today + timedelta(days=100)).strftime("%Y-%m-%d %H:%M:%S")

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
        "https://bssadmin.stampedecom.in/eapi/api/v1/searchCustomerData",
        json=payload,
        headers=headers
    )

    return response.json()