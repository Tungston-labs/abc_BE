# from django.core.management.base import BaseCommand
# from django.db import close_old_connections, OperationalError
# from lcos.models import LCOISPMapping
# from network.services.isp_handler import fetch_isp_data
# from customers.models import Customer
# from datetime import datetime
# import traceback


# class Command(BaseCommand):
#     help = "Fetch ISP Data and update customer expiry dates"

#     def handle(self, *args, **kwargs):
#         print("🚀 Starting ISP expiry update...")

#         mappings = LCOISPMapping.objects.filter(is_active=True)

#         total_updated = 0
#         total_not_found = 0

#         for mapping in mappings:
#             # Close stale DB connections before processing each mapping
#             close_old_connections()

#             print(f"\n🔌 Processing ISP: {mapping.partner_name}")

#             try:
#                 data = fetch_isp_data(mapping)

#                 data_list = data.get("data", [])

#                 updated = 0
#                 not_found = 0

#                 for item in data_list:
#                     result = update_expiry(item)

#                     if result == "updated":
#                         updated += 1
#                     elif result == "not_found":
#                         not_found += 1

#                 print(
#                     f"✔ {mapping.partner_name} → Updated: {updated}, Not Found: {not_found}"
#                 )

#                 total_updated += updated
#                 total_not_found += not_found

#             except Exception:
#                 print(f"\n❌ Error for {mapping.partner_name}")
#                 traceback.print_exc()

#         print("\n🎯 FINAL SUMMARY")
#         print(f"✅ Total Updated: {total_updated}")
#         print(f"❌ Total Not Found: {total_not_found}")
#         print("🏁 Done.")


# # ==========================
# # HELPER FUNCTIONS
# # ==========================

# def normalize_mac(mac):
#     if not mac:
#         return None
#     return mac.lower().replace(":", "").replace("-", "")


# def get_customer_by_username(username):
#     """
#     Retry once if PostgreSQL connection was dropped.
#     """
#     try:
#         return Customer.objects.filter(username__iexact=username).first()

#     except OperationalError:
#         print("⚠ Database connection lost. Reconnecting...")
#         close_old_connections()
#         return Customer.objects.filter(username__iexact=username).first()


# def get_customer_by_mac(mac):
#     """
#     Retry once if PostgreSQL connection was dropped.
#     """
#     try:
#         return Customer.objects.filter(mac_id__iexact=mac).first()

#     except OperationalError:
#         print("⚠ Database connection lost. Reconnecting...")
#         close_old_connections()
#         return Customer.objects.filter(mac_id__iexact=mac).first()


# def update_expiry(item):
#     close_old_connections()

#     username = item.get("username")
#     mac = normalize_mac(item.get("macAddress"))
#     plan_name = item.get("planName")

#     if username:
#         username = username.strip().lower()

#     # Treat empty plan names as None
#     if isinstance(plan_name, str):
#         plan_name = plan_name.strip()
#         if not plan_name:
#             plan_name = None

#     expiry_str = item.get("expiryDate")

#     if not expiry_str:
#         print(f"❌ Missing expiry for {username}")
#         return "not_found"

#     # Parse both ISP date formats
#     try:
#         try:
#             expiry_date = datetime.strptime(
#                 expiry_str,
#                 "%d-%b-%Y %H:%M:%S"
#             ).date()
#         except ValueError:
#             expiry_date = datetime.strptime(
#                 expiry_str,
#                 "%m/%d/%Y %I:%M:%S %p"
#             ).date()

#     except Exception:
#         print(f"❌ Invalid date format: {expiry_str}")
#         return "not_found"

#     customer = None

#     if username:
#         customer = get_customer_by_username(username)

#     if not customer and mac:
#         customer = get_customer_by_mac(mac)

#     if not customer:
#         print(f"❌ Not found: {username}")
#         return "not_found"

#     fields_to_update = []

#     # Update expiry date if changed
#     if customer.expiry_date != expiry_date:
#         customer.expiry_date = expiry_date
#         fields_to_update.append("expiry_date")

#     # Update plan only if ISP returned a non-empty value
#     if (
#         plan_name is not None
#         and plan_name != ""
#         and customer.plan != plan_name
#     ):
#         customer.plan = plan_name
#         fields_to_update.append("plan")

#     if not fields_to_update:
#         return "skipped"

#     try:
#         customer.save(update_fields=fields_to_update)
#         print(
#             f"✅ Updated: {customer.username} ({', '.join(fields_to_update)})"
#         )
#         return "updated"

#     except OperationalError:
#         print("⚠ Database connection lost while saving. Retrying...")
#         close_old_connections()

#         customer = Customer.objects.get(pk=customer.pk)

#         if "expiry_date" in fields_to_update:
#             customer.expiry_date = expiry_date

#         if "plan" in fields_to_update:
#             customer.plan = plan_name

#         customer.save(update_fields=fields_to_update)

#         print(
#             f"✅ Updated: {customer.username} ({', '.join(fields_to_update)})"
#         )
#         return "updated"



from django.core.management.base import BaseCommand
from django.db import close_old_connections, OperationalError
from lcos.models import LCOISPMapping
from network.services.isp_handler import fetch_isp_data
from customers.models import Customer
from datetime import datetime
import traceback


class Command(BaseCommand):
    help = "Fetch ISP Data and update/create customer records"

    def handle(self, *args, **kwargs):
        print("🚀 Starting ISP expiry update...")

        mappings = LCOISPMapping.objects.filter(
            is_active=True
        ).select_related("lco", "isp")

        total_updated = 0
        total_created = 0
        total_not_found = 0

        for mapping in mappings:

            # Close stale DB connections before processing each mapping
            close_old_connections()

            print(f"\n🔌 Processing ISP: {mapping.partner_name}")
            print(f"🏢 LCO: {mapping.lco}")
            print(f"📡 ISP: {mapping.isp}")

            try:
                data = fetch_isp_data(mapping)

                data_list = data.get("data", [])

                updated = 0
                created = 0
                not_found = 0

                for item in data_list:

                    result = update_expiry(
                        item,
                        mapping
                    )

                    if result == "updated":
                        updated += 1

                    elif result == "created":
                        created += 1

                    elif result == "not_found":
                        not_found += 1

                print(
                    f"✔ {mapping.partner_name} → "
                    f"Updated: {updated}, "
                    f"Created: {created}, "
                    f"Not Found: {not_found}"
                )

                total_updated += updated
                total_created += created
                total_not_found += not_found

            except Exception:
                print(
                    f"\n❌ Error for {mapping.partner_name}"
                )
                traceback.print_exc()

        print("\n🎯 FINAL SUMMARY")
        print(f"✅ Total Updated: {total_updated}")
        print(f"🆕 Total Created: {total_created}")
        print(f"❌ Total Not Found: {total_not_found}")
        print("🏁 Done.")


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def normalize_mac(mac):
    if not mac:
        return None

    return (
        mac.lower()
        .replace(":", "")
        .replace("-", "")
        .strip()
    )


def get_customer_by_username(username):
    """
    Retry once if PostgreSQL connection was dropped.
    """

    try:
        return Customer.objects.filter(
            username__iexact=username
        ).first()

    except OperationalError:
        print(
            "⚠ Database connection lost. Reconnecting..."
        )

        close_old_connections()

        return Customer.objects.filter(
            username__iexact=username
        ).first()


def get_customer_by_mac(mac):
    """
    Retry once if PostgreSQL connection was dropped.
    """

    try:
        return Customer.objects.filter(
            mac_id__iexact=mac
        ).first()

    except OperationalError:
        print(
            "⚠ Database connection lost. Reconnecting..."
        )

        close_old_connections()

        return Customer.objects.filter(
            mac_id__iexact=mac
        ).first()


def create_customer(item, mapping, username, mac, expiry_date, plan_name):
    """
    Create a new customer using ISP data.

    LCO and ISP are taken from the LCOISPMapping.
    """

    full_name = item.get("full_name")
    phone = item.get("phone")
    email = item.get("email")
    address = item.get("address")

    # Clean empty strings
    if isinstance(full_name, str):
        full_name = full_name.strip() or None

    if isinstance(phone, str):
        phone = phone.strip() or None

    if isinstance(email, str):
        email = email.strip() or None

    if isinstance(address, str):
        address = address.strip() or None

    customer = Customer.objects.create(
        full_name=full_name,
        username=username,
        phone=phone,
        address=address,
        email=email,
        mac_id=mac,
        plan=plan_name,
        isp=mapping.isp,
        lco=mapping.lco,
        expiry_date=expiry_date,
    )

    print(
        f"🆕 Created Customer: {customer.username} | "
        f"Name: {customer.full_name} | "
        f"LCO: {mapping.lco} | "
        f"ISP: {mapping.isp}"
    )

    return customer


def update_expiry(item, mapping):

    # Close stale DB connection before each item
    close_old_connections()

    # =====================================================
    # ISP CUSTOMER DATA
    # =====================================================

    username = item.get("username")
    mac = normalize_mac(
        item.get("macAddress")
    )

    plan_name = item.get("planName")

    full_name = item.get("full_name")
    phone = item.get("phone")
    email = item.get("email")
    address = item.get("address")

    # Normalize username
    if username:
        username = username.strip().lower()

    # Normalize plan
    if isinstance(plan_name, str):
        plan_name = plan_name.strip()

        if not plan_name:
            plan_name = None

    # =====================================================
    # EXPIRY DATE
    # =====================================================

    expiry_str = item.get("expiryDate")

    if not expiry_str:
        print(
            f"❌ Missing expiry for {username}"
        )
        return "not_found"

    # =====================================================
    # PARSE ISP DATE FORMATS
    # =====================================================

    try:

        try:
            # Stampede
            expiry_date = datetime.strptime(
                expiry_str,
                "%d-%b-%Y %H:%M:%S"
            ).date()

        except ValueError:

            # Xtra Net / WEONE
            expiry_date = datetime.strptime(
                expiry_str,
                "%m/%d/%Y %I:%M:%S %p"
            ).date()

    except Exception:

        print(
            f"❌ Invalid date format: {expiry_str}"
        )

        return "not_found"

    # =====================================================
    # FIND EXISTING CUSTOMER
    # =====================================================

    customer = None

    # 1️⃣ Match by username
    if username:

        customer = get_customer_by_username(
            username
        )

    # 2️⃣ Fallback to MAC
    if not customer and mac:

        customer = get_customer_by_mac(
            mac
        )

    # =====================================================
    # CREATE NEW CUSTOMER
    # =====================================================

    if not customer:

        print(
            f"🆕 Customer not found: {username}"
        )

        # Username is required for automatic creation
        if not username:

            print(
                "❌ Cannot create customer because "
                "username is missing"
            )

            return "not_found"

        try:

            create_customer(
                item=item,
                mapping=mapping,
                username=username,
                mac=mac,
                expiry_date=expiry_date,
                plan_name=plan_name,
            )

            return "created"

        except OperationalError:

            print(
                "⚠ Database connection lost "
                "while creating customer. Retrying..."
            )

            close_old_connections()

            create_customer(
                item=item,
                mapping=mapping,
                username=username,
                mac=mac,
                expiry_date=expiry_date,
                plan_name=plan_name,
            )

            return "created"

    # =====================================================
    # EXISTING CUSTOMER
    # =====================================================

    fields_to_update = []

    # =====================================================
    # UPDATE EXPIRY
    # =====================================================

    if customer.expiry_date != expiry_date:

        customer.expiry_date = expiry_date

        fields_to_update.append(
            "expiry_date"
        )

    # =====================================================
    # UPDATE PLAN
    # Only when ISP returned a non-empty plan
    # =====================================================

    if (
        plan_name is not None
        and customer.plan != plan_name
    ):

        customer.plan = plan_name

        fields_to_update.append(
            "plan"
        )

    # =====================================================
    # NOTHING TO UPDATE
    # =====================================================

    if not fields_to_update:

        return "skipped"

    # =====================================================
    # SAVE EXISTING CUSTOMER
    # =====================================================

    try:

        customer.save(
            update_fields=fields_to_update
        )

        print(
            f"✅ Updated: {customer.username} "
            f"({', '.join(fields_to_update)})"
        )

        return "updated"

    except OperationalError:

        print(
            "⚠ Database connection lost "
            "while saving. Retrying..."
        )

        close_old_connections()

        customer = Customer.objects.get(
            pk=customer.pk
        )

        if "expiry_date" in fields_to_update:

            customer.expiry_date = expiry_date

        if "plan" in fields_to_update:

            customer.plan = plan_name

        customer.save(
            update_fields=fields_to_update
        )

        print(
            f"✅ Updated: {customer.username} "
            f"({', '.join(fields_to_update)})"
        )

        return "updated"