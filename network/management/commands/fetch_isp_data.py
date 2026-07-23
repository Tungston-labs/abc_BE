from django.core.management.base import BaseCommand
from django.db import close_old_connections, OperationalError
from lcos.models import LCOISPMapping
from network.services.isp_handler import fetch_isp_data
from customers.models import Customer
from datetime import datetime
import traceback


class Command(BaseCommand):
    help = "Fetch ISP Data and update customer expiry dates"

    def handle(self, *args, **kwargs):
        print("🚀 Starting ISP expiry update...")

        mappings = LCOISPMapping.objects.filter(is_active=True)

        total_updated = 0
        total_not_found = 0

        for mapping in mappings:
            # Close stale DB connections before processing each mapping
            close_old_connections()

            print(f"\n🔌 Processing ISP: {mapping.partner_name}")

            try:
                data = fetch_isp_data(mapping)

                data_list = data.get("data", [])

                updated = 0
                not_found = 0

                for item in data_list:
                    result = update_expiry(item)

                    if result == "updated":
                        updated += 1
                    elif result == "not_found":
                        not_found += 1

                print(
                    f"✔ {mapping.partner_name} → Updated: {updated}, Not Found: {not_found}"
                )

                total_updated += updated
                total_not_found += not_found

            except Exception:
                print(f"\n❌ Error for {mapping.partner_name}")
                traceback.print_exc()

        print("\n🎯 FINAL SUMMARY")
        print(f"✅ Total Updated: {total_updated}")
        print(f"❌ Total Not Found: {total_not_found}")
        print("🏁 Done.")


# ==========================
# HELPER FUNCTIONS
# ==========================

def normalize_mac(mac):
    if not mac:
        return None
    return mac.lower().replace(":", "").replace("-", "")


def get_customer_by_username(username):
    """
    Retry once if PostgreSQL connection was dropped.
    """
    try:
        return Customer.objects.filter(username__iexact=username).first()

    except OperationalError:
        print("⚠ Database connection lost. Reconnecting...")
        close_old_connections()
        return Customer.objects.filter(username__iexact=username).first()


def get_customer_by_mac(mac):
    """
    Retry once if PostgreSQL connection was dropped.
    """
    try:
        return Customer.objects.filter(mac_id__iexact=mac).first()

    except OperationalError:
        print("⚠ Database connection lost. Reconnecting...")
        close_old_connections()
        return Customer.objects.filter(mac_id__iexact=mac).first()


def update_expiry(item):
    # Close stale DB connections before each query
    close_old_connections()

    username = item.get("username")
    mac = normalize_mac(item.get("macAddress"))

    if username:
        username = username.strip().lower()

    expiry_str = item.get("expiryDate")

    if not expiry_str:
        print(f"❌ Missing expiry for {username}")
        return "not_found"

    # Parse both ISP date formats
    try:
        try:
            # Stampede
            expiry_date = datetime.strptime(
                expiry_str,
                "%d-%b-%Y %H:%M:%S"
            ).date()

        except ValueError:
            # Extranet
            expiry_date = datetime.strptime(
                expiry_str,
                "%m/%d/%Y %I:%M:%S %p"
            ).date()

    except Exception:
        print(f"❌ Invalid date format: {expiry_str}")
        return "not_found"

    customer = None

    # Match by username
    if username:
        customer = get_customer_by_username(username)

    # Fallback to MAC
    if not customer and mac:
        customer = get_customer_by_mac(mac)

    if not customer:
        print(f"❌ Not found: {username}")
        return "not_found"

    # Update expiry if changed
    if customer.expiry_date != expiry_date:
        try:
            customer.expiry_date = expiry_date
            customer.save(update_fields=["expiry_date"])
            print(f"✅ Updated: {customer.username}")
            return "updated"

        except OperationalError:
            print("⚠ Database connection lost while saving. Retrying...")
            close_old_connections()

            customer = Customer.objects.get(pk=customer.pk)
            customer.expiry_date = expiry_date
            customer.save(update_fields=["expiry_date"])

            print(f"✅ Updated: {customer.username}")
            return "updated"

    return "skipped"