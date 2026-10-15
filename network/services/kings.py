import requests
from datetime import datetime, timedelta


KINGS_API_URL = (
    "https://bb.inygo.in/eapi/api/v1/searchCustomerData"
)


def fetch_kings_data(mapping):
    isp = mapping.isp

    print("\n========== KINGS ISP ==========")
    print(f"Partner Name : {mapping.partner_name}")

    token = isp.token

    if not token:
        raise Exception("Kings ISP token is missing")

    today = datetime.now()

    from_date = (
        today - timedelta(days=200)
    ).strftime("%Y-%m-%d %H:%M:%S")

    to_date = (
        today + timedelta(days=200)
    ).strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "partnerName": mapping.partner_name,
        "expiryFrom": from_date,
        "expiryTill": to_date,
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    response = requests.post(
        KINGS_API_URL,
        json=payload,
        headers=headers,
        timeout=60,
    )

    response.raise_for_status()

    result = response.json()
    customers = result.get("data", [])

    normalized = []

    for customer in customers:
        normalized.append({
            "username": customer.get("username"),
            "macAddress": customer.get("macAddress"),
            "expiryDate": customer.get("expiryDate"),
            "planName": customer.get("planName"),

            "full_name": customer.get("customerName"),
            "phone": customer.get("phone"),
            "email": customer.get("email"),
            "address": customer.get("address"),

            "status": customer.get("status"),

            # Kings-specific fields
            "operatorName": customer.get("operatorName"),
            "sessionStatus": customer.get("sessionStatus"),
            "subscriptionDetails": customer.get(
                "subscriptionDetails"
            ),
        })

    print(f"Kings Customers Received: {len(normalized)}")

    return {
        "data": normalized
    }