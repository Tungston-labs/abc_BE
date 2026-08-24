import requests
from datetime import datetime, timedelta
from django.conf import settings


TOKEN_URL = (
    "https://admin.extranet.co.in/"
    "H8IntegrationApi/Token"
)

CUSTOMER_URL = (
    "https://admin.extranet.co.in/"
    "H8IntegrationApi/CustomerExpiryDetails"
)


def get_token():

    payload = {
        "Username": settings.EXTRANET_USERNAME,
        "Password": settings.EXTRANET_PASSWORD,
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(
        TOKEN_URL,
        json=payload,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    print("Token Response:", data)

    token = (
        data.get("token")
        or data.get("Token")
        or data.get("access_token")
        or data.get("result")
    )

    if not token:
        raise Exception(
            f"Unable to fetch token. Response: {data}"
        )

    return token


def fetch_extranet_data(mapping):

    print("\n========== EXTRANET ==========")
    print(
        f"Partner Code : {mapping.partner_name}"
    )

    token = get_token()

    today = datetime.now()

    from_date = (
        today - timedelta(days=200)
    ).strftime("%Y-%m-%d %H:%M:%S")

    to_date = (
        today + timedelta(days=200)
    ).strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "partnercode": mapping.partner_name,
        "FromDate": from_date,
        "ToDate": to_date
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        CUSTOMER_URL,
        json=payload,
        headers=headers,
        timeout=60
    )

    response.raise_for_status()

    data = response.json()

    normalized = []

    for customer in data.get("result", []):

        normalized.append({
            "username": customer.get("Username"),
            "macAddress": customer.get("MAC_address"),
            "expiryDate": customer.get("ExpiryDate"),
            "planName": customer.get("PlanName"),

            "full_name": customer.get("CustomerName"),
            "phone": customer.get("PhoneNumber"),
            "email": customer.get("Email"),
            "address": customer.get("Address"),

            # IMPORTANT
            "status": customer.get("Status"),
        })

    print(
        f"XTRA NET Customers Received: "
        f"{len(normalized)}"
    )

    return {
        "data": normalized
    }