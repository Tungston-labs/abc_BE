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

    help = "Fetch ISP Data and synchronize customers"


    def handle(self, *args, **kwargs):

        print("🚀 Starting ISP customer sync...")

        mappings = LCOISPMapping.objects.filter(
            is_active=True
        ).select_related(
            "lco",
            "isp"
        )

        total_updated = 0
        total_created = 0
        total_skipped = 0
        total_inactive = 0

        for mapping in mappings:

            close_old_connections()

            print(
                f"\n🔌 Processing ISP: "
                f"{mapping.partner_name}"
            )

            print(
                f"🏢 LCO: {mapping.lco}"
            )

            print(
                f"📡 ISP: {mapping.isp.name}"
            )

            try:

                data = fetch_isp_data(mapping)

                data_list = data.get(
                    "data",
                    []
                )

                updated = 0
                created = 0
                skipped = 0
                inactive = 0

                for item in data_list:

                    result = sync_customer(
                        item,
                        mapping
                    )

                    if result == "created":
                        created += 1

                    elif result == "updated":
                        updated += 1

                    elif result == "skipped":
                        skipped += 1

                    elif result == "inactive":
                        inactive += 1

                print(
                    f"\n✔ {mapping.partner_name}"
                )

                print(
                    f"   Created  : {created}"
                )

                print(
                    f"   Updated  : {updated}"
                )

                print(
                    f"   Skipped  : {skipped}"
                )

                print(
                    f"   Inactive : {inactive}"
                )

                total_created += created
                total_updated += updated
                total_skipped += skipped
                total_inactive += inactive

            except Exception:

                print(
                    f"\n❌ Error for "
                    f"{mapping.partner_name}"
                )

                traceback.print_exc()

        print("\n🎯 FINAL SUMMARY")

        print(
            f"🆕 Total Created: "
            f"{total_created}"
        )

        print(
            f"✅ Total Updated: "
            f"{total_updated}"
        )

        print(
            f"⏭ Total Skipped: "
            f"{total_skipped}"
        )

        print(
            f"🚫 Total Inactive: "
            f"{total_inactive}"
        )

        print("🏁 Done.")


# ============================================================
# HELPERS
# ============================================================


def clean_value(value):

    if value is None:
        return None

    if isinstance(value, str):

        value = value.strip()

        if not value:
            return None

    return value


def normalize_username(username):

    username = clean_value(username)

    if username:
        return username.lower()

    return None


def get_customer_by_username(username):

    try:

        return Customer.objects.filter(
            username__iexact=username
        ).first()

    except OperationalError:

        print(
            "⚠ Database connection lost. "
            "Reconnecting..."
        )

        close_old_connections()

        return Customer.objects.filter(
            username__iexact=username
        ).first()


def get_customer_by_mac(mac):

    if not mac:
        return None

    try:

        return Customer.objects.filter(
            mac_id__iexact=mac
        ).first()

    except OperationalError:

        print(
            "⚠ Database connection lost. "
            "Reconnecting..."
        )

        close_old_connections()

        return Customer.objects.filter(
            mac_id__iexact=mac
        ).first()


def parse_expiry_date(expiry_str):

    expiry_str = clean_value(expiry_str)

    if not expiry_str:
        return None

    formats = [
        "%d-%b-%Y %H:%M:%S",
        "%m/%d/%Y %I:%M:%S %p",
    ]

    for date_format in formats:

        try:

            return datetime.strptime(
                expiry_str,
                date_format
            ).date()

        except ValueError:
            continue

    return None


def sync_customer(item, mapping):

    close_old_connections()

    # ========================================================
    # BASIC DATA
    # ========================================================

    username = normalize_username(
        item.get("username")
    )

    if not username:

        print(
            "⏭ Skipped: API record has no username"
        )

        return "skipped"


    # ========================================================
    # STATUS CHECK
    # ========================================================

    status = clean_value(
        item.get("status")
    )

    if not status:

        print(
            f"⏭ Skipped: {username} "
            f"(status missing)"
        )

        return "skipped"


    if status.lower() != "active":

        print(
            f"🚫 Inactive: {username}"
        )

        return "inactive"


    # ========================================================
    # API VALUES
    # ========================================================

    original_mac = clean_value(
        item.get("macAddress")
    )

    plan_name = clean_value(
        item.get("planName")
    )

    expiry_str = clean_value(
        item.get("expiryDate")
    )

    expiry_date = parse_expiry_date(
        expiry_str
    )


    # ========================================================
    # FIND CUSTOMER
    # ========================================================

    customer = get_customer_by_username(
        username
    )


    # ========================================================
    # FALLBACK MAC MATCH
    # ========================================================

    if not customer and original_mac:

        customer = get_customer_by_mac(
            original_mac
        )


    # ========================================================
    # CREATE NEW CUSTOMER
    # ========================================================

    if not customer:

        customer = Customer(
            full_name=clean_value(
                item.get("full_name")
            ),

            username=username,

            phone=clean_value(
                item.get("phone")
            ),

            email=clean_value(
                item.get("email")
            ),

            address=clean_value(
                item.get("address")
            ),

            mac_id=original_mac,

            plan=plan_name,

            expiry_date=expiry_date,

            lco=mapping.lco,

            isp=mapping.isp,
        )

        try:

            customer.save()

            print(
                f"🆕 Created: {username}"
            )

            return "created"

        except OperationalError:

            print(
                "⚠ Database connection lost "
                "while creating. Retrying..."
            )

            close_old_connections()

            customer.save()

            print(
                f"🆕 Created: {username}"
            )

            return "created"


    # ========================================================
    # UPDATE EXISTING CUSTOMER
    # ========================================================

    fields_to_update = []


    # --------------------------------------------------------
    # MAC
    # --------------------------------------------------------

    # IMPORTANT:
    # Save exactly what ISP returned.
    #
    # Example:
    # API       = 44:95:3b:e2:69:e1
    # DB old    = 44953be2e69e1
    #
    # It will update DB to:
    # 44:95:3b:e2:69:e1
    # --------------------------------------------------------

    if (
        original_mac
        and customer.mac_id != original_mac
    ):

        customer.mac_id = original_mac

        fields_to_update.append(
            "mac_id"
        )


    # --------------------------------------------------------
    # EXPIRY
    # --------------------------------------------------------

    if (
        expiry_date
        and customer.expiry_date != expiry_date
    ):

        customer.expiry_date = expiry_date

        fields_to_update.append(
            "expiry_date"
        )


    # --------------------------------------------------------
    # PLAN
    # --------------------------------------------------------

    # Do NOT overwrite existing plan
    # when ISP plan is empty/null.

    if (
        plan_name is not None
        and customer.plan != plan_name
    ):

        customer.plan = plan_name

        fields_to_update.append(
            "plan"
        )


    # --------------------------------------------------------
    # CUSTOMER NAME
    # --------------------------------------------------------

    full_name = clean_value(
        item.get("full_name")
    )

    if (
        full_name
        and customer.full_name != full_name
    ):

        customer.full_name = full_name

        fields_to_update.append(
            "full_name"
        )


    # --------------------------------------------------------
    # PHONE
    # --------------------------------------------------------

    phone = clean_value(
        item.get("phone")
    )

    if (
        phone
        and customer.phone != phone
    ):

        customer.phone = phone

        fields_to_update.append(
            "phone"
        )


    # --------------------------------------------------------
    # EMAIL
    # --------------------------------------------------------

    email = clean_value(
        item.get("email")
    )

    if (
        email
        and customer.email != email
    ):

        customer.email = email

        fields_to_update.append(
            "email"
        )


    # --------------------------------------------------------
    # ADDRESS
    # --------------------------------------------------------

    address = clean_value(
        item.get("address")
    )

    if (
        address
        and customer.address != address
    ):

        customer.address = address

        fields_to_update.append(
            "address"
        )


    # --------------------------------------------------------
    # LCO
    # --------------------------------------------------------

    if customer.lco_id != mapping.lco_id:

        customer.lco = mapping.lco

        fields_to_update.append(
            "lco"
        )


    # --------------------------------------------------------
    # ISP
    # --------------------------------------------------------

    if customer.isp_id != mapping.isp_id:

        customer.isp = mapping.isp

        fields_to_update.append(
            "isp"
        )


    # ========================================================
    # NOTHING CHANGED
    # ========================================================

    if not fields_to_update:

        print(
            f"⏭ Skipped: {username}"
        )

        return "skipped"


    # ========================================================
    # SAVE
    # ========================================================

    try:

        customer.save(
            update_fields=fields_to_update
        )

        print(
            f"✅ Updated: {username} "
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

        customer.save(
            update_fields=fields_to_update
        )

        print(
            f"✅ Updated: {username} "
            f"({', '.join(fields_to_update)})"
        )

        return "updated"