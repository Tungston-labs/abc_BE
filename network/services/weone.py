import requests
from datetime import datetime, timedelta
from django.conf import settings


TOKEN_URL = (
    "https://adminisp.weonebroadband.com/"
    "H8IntegrationApi/Token"
)

CUSTOMER_URL = (
    "https://adminisp.weonebroadband.com/"
    "H8IntegrationApi/CustomerExpiryDetails"
)


def get_token():

    payload = {
        "Username": settings.WEONE_USERNAME,
        "Password": settings.WEONE_PASSWORD,
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

    print(
        "WEONE Token Response:",
        {
            "returnCode": data.get("returnCode"),
            "returnMessage": data.get("returnMessage"),
            "TokenTimeout": data.get("TokenTimeout"),
        }
    )

    token = data.get("Token")

    if not token:
        raise Exception(
            f"Unable to fetch WEONE token. "
            f"Response: {data}"
        )

    return token


def fetch_weone_data(mapping):

    print("\n========== WEONE ==========")
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

    print(
        f"WEONE API Response: "
        f"Code={data.get('errorCode')}, "
        f"Message={data.get('errorMessage')}"
    )

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
        f"WEONE Customers Received: "
        f"{len(normalized)}"
    )

    return {
        "data": normalized
    }