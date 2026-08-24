import requests
from datetime import datetime, timedelta


def fetch_stampede_data(mapping):
    isp = mapping.isp

    print("\n========== STAMPEDE ==========")
    print(f"Partner Name : {mapping.partner_name}")

    token = isp.token

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
        "expiryTill": to_date
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        "https://bssadmin.stampedecom.in/eapi/api/v1/searchCustomerData",
        json=payload,
        headers=headers,
        timeout=60
    )

    response.raise_for_status()

    data = response.json()

    normalized = []

    for customer in data.get("data", []):

        normalized.append({
            "username": customer.get("username"),
            "macAddress": customer.get("macAddress"),
            "expiryDate": customer.get("expiryDate"),
            "planName": customer.get("planName"),

            "full_name": customer.get("customerName"),
            "phone": customer.get("phone"),
            "email": customer.get("email"),
            "address": customer.get("address"),

            # IMPORTANT
            "status": customer.get("status"),
        })

    print(
        f"Stampede Customers Received: {len(normalized)}"
    )

    return {
        "data": normalized
    }