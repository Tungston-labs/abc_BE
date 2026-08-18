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
    help = "Fetch ISP Data, update existing customers and create new customers"

    def handle(self, *args, **kwargs):
        print("🚀 Starting ISP customer sync...")

        mappings = LCOISPMapping.objects.filter(
            is_active=True
        ).select_related("lco", "isp")

        total_updated = 0
        total_created = 0
        total_not_found = 0

        for mapping in mappings:
            close_old_connections()

            print(f"\n🔌 Processing ISP: {mapping.partner_name}")
            print(f"🏢 LCO: {mapping.lco}")
            print(f"📡 ISP: {mapping.isp.name}")

            try:
                data = fetch_isp_data(mapping)

                data_list = data.get("data", [])

                updated = 0
                created = 0
                not_found = 0

                for item in data_list:

                    result = sync_customer(
                        item=item,
                        mapping=mapping
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


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_value(value):
    """
    Convert empty strings / whitespace to None.
    """
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return None

    return value


def normalize_mac(mac):
    """
    Used ONLY for comparison/searching.

    Example:
        bc:62:d2:87:72:09
        ->
        bc62d2877209

    The normalized value is NEVER saved to Customer.mac_id.
    """
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
    Find customer by username.
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
    Find customer using normalized MAC.

    This handles existing customers whose MAC may have been
    stored without ':'.

    Example:

    DB:
        44953be28a81

    ISP:
        44:95:3b:e2:8a:81

    Both will match.
    """

    if not mac:
        return None

    normalized_mac = normalize_mac(mac)

    if not normalized_mac:
        return None

    try:
        # First try exact response format
        customer = Customer.objects.filter(
            mac_id__iexact=mac
        ).first()

        if customer:
            return customer

        # If not found, compare against existing records
        # after removing ':' and '-'.
        customers = Customer.objects.exclude(
            mac_id__isnull=True
        ).exclude(
            mac_id=""
        )

        for customer in customers:

            existing_normalized_mac = normalize_mac(
                customer.mac_id
            )

            if existing_normalized_mac == normalized_mac:
                return customer

        return None

    except OperationalError:
        print(
            "⚠ Database connection lost. Reconnecting..."
        )

        close_old_connections()

        return get_customer_by_mac(mac)


def parse_expiry_date(expiry_str):
    """
    Supports:

    Stampede:
        04-Sep-2026 23:59:59

    Xtra Net / WEONE:
        8/19/2026 11:59:59 PM
    """

    if not expiry_str:
        return None

    try:

        try:
            # Stampede
            return datetime.strptime(
                expiry_str,
                "%d-%b-%Y %H:%M:%S"
            ).date()

        except ValueError:

            # Xtra Net / WEONE
            return datetime.strptime(
                expiry_str,
                "%m/%d/%Y %I:%M:%S %p"
            ).date()

    except Exception:
        print(
            f"❌ Invalid date format: {expiry_str}"
        )

        return None


# ============================================================
# CREATE / UPDATE CUSTOMER
# ============================================================

def sync_customer(item, mapping):

    close_old_connections()

    # --------------------------------------------------------
    # Values coming from normalized ISP response
    # --------------------------------------------------------

    username = clean_value(
        item.get("username")
    )

    original_mac = clean_value(
        item.get("macAddress")
    )

    plan_name = clean_value(
        item.get("planName")
    )

    expiry_str = clean_value(
        item.get("expiryDate")
    )

    full_name = clean_value(
        item.get("customerName")
    )

    phone = clean_value(
        item.get("phone")
    )

    email = clean_value(
        item.get("email")
    )

    address = clean_value(
        item.get("address")
    )

    # --------------------------------------------------------
    # Username is required for new customer creation
    # --------------------------------------------------------

    if not username:
        print(
            "❌ Username missing. Cannot create/update customer."
        )

        return "not_found"

    username = username.lower()

    # --------------------------------------------------------
    # Parse expiry
    # --------------------------------------------------------

    expiry_date = parse_expiry_date(
        expiry_str
    )

    if not expiry_date:
        print(
            f"❌ Invalid/missing expiry for {username}"
        )

        return "not_found"

    # --------------------------------------------------------
    # Find existing customer
    # --------------------------------------------------------

    customer = get_customer_by_username(
        username
    )

    # --------------------------------------------------------
    # If username doesn't match, try MAC
    # --------------------------------------------------------

    if not customer and original_mac:

        customer = get_customer_by_mac(
            original_mac
        )

        if customer:
            print(
                f"🔎 Customer matched by MAC: "
                f"{username} → {customer.username}"
            )

    # ========================================================
    # EXISTING CUSTOMER
    # ========================================================

    if customer:

        fields_to_update = []

        # ----------------------------------------------------
        # Update username if customer was found by MAC
        # ----------------------------------------------------

        if (
            username
            and customer.username != username
        ):
            customer.username = username
            fields_to_update.append("username")

        # ----------------------------------------------------
        # Update expiry
        # ----------------------------------------------------

        if customer.expiry_date != expiry_date:

            customer.expiry_date = expiry_date

            fields_to_update.append(
                "expiry_date"
            )

        # ----------------------------------------------------
        # Update plan ONLY if ISP returned a value
        # ----------------------------------------------------

        if (
            plan_name is not None
            and customer.plan != plan_name
        ):

            customer.plan = plan_name

            fields_to_update.append(
                "plan"
            )

        # ----------------------------------------------------
        # IMPORTANT:
        # Save MAC EXACTLY as ISP response
        #
        # Example:
        # ISP -> bc:62:d2:87:72:09
        #
        # DB will become:
        # bc:62:d2:87:72:09
        #
        # NOT:
        # bc62d2877209
        # ----------------------------------------------------

        if (
            original_mac
            and customer.mac_id != original_mac
        ):

            customer.mac_id = original_mac

            fields_to_update.append(
                "mac_id"
            )

        # ----------------------------------------------------
        # Update other customer details when available
        # ----------------------------------------------------

        if (
            full_name is not None
            and customer.full_name != full_name
        ):

            customer.full_name = full_name

            fields_to_update.append(
                "full_name"
            )

        if (
            phone is not None
            and customer.phone != phone
        ):

            customer.phone = phone

            fields_to_update.append(
                "phone"
            )

        if (
            email is not None
            and customer.email != email
        ):

            customer.email = email

            fields_to_update.append(
                "email"
            )

        if (
            address is not None
            and customer.address != address
        ):

            customer.address = address

            fields_to_update.append(
                "address"
            )

        # ----------------------------------------------------
        # Ensure LCO and ISP are correct
        # ----------------------------------------------------

        if customer.lco_id != mapping.lco_id:

            customer.lco_id = mapping.lco_id

            fields_to_update.append(
                "lco"
            )

        if customer.isp_id != mapping.isp_id:

            customer.isp_id = mapping.isp_id

            fields_to_update.append(
                "isp"
            )

        # ----------------------------------------------------
        # Nothing changed
        # ----------------------------------------------------

        if not fields_to_update:

            print(
                f"⏭ Skipped: {username}"
            )

            return "skipped"

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

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
                "⚠ Database connection lost while saving. "
                "Retrying..."
            )

            close_old_connections()

            customer = Customer.objects.get(
                pk=customer.pk
            )

            # Re-apply values

            if "username" in fields_to_update:
                customer.username = username

            if "expiry_date" in fields_to_update:
                customer.expiry_date = expiry_date

            if "plan" in fields_to_update:
                customer.plan = plan_name

            if "mac_id" in fields_to_update:
                customer.mac_id = original_mac

            if "full_name" in fields_to_update:
                customer.full_name = full_name

            if "phone" in fields_to_update:
                customer.phone = phone

            if "email" in fields_to_update:
                customer.email = email

            if "address" in fields_to_update:
                customer.address = address

            if "lco" in fields_to_update:
                customer.lco_id = mapping.lco_id

            if "isp" in fields_to_update:
                customer.isp_id = mapping.isp_id

            customer.save(
                update_fields=fields_to_update
            )

            print(
                f"✅ Updated after retry: "
                f"{customer.username}"
            )

            return "updated"

    # ========================================================
    # NEW CUSTOMER
    # ========================================================

    print(
        f"🆕 New customer found from ISP: {username}"
    )

    try:

        customer = Customer.objects.create(

            # ISP response
            full_name=full_name,
            username=username,
            phone=phone,
            email=email,
            address=address,

            # IMPORTANT:
            # Store MAC exactly as received
            mac_id=original_mac,

            plan=plan_name,
            expiry_date=expiry_date,

            # From LCOISPMapping
            lco=mapping.lco,
            isp=mapping.isp,
        )

        print(
            f"🆕 Created customer: "
            f"{customer.username}"
        )

        print(
            f"   LCO : {mapping.lco}"
        )

        print(
            f"   ISP : {mapping.isp.name}"
        )

        print(
            f"   MAC : {original_mac}"
        )

        return "created"

    except OperationalError:

        print(
            "⚠ Database connection lost while creating. "
            "Retrying..."
        )

        close_old_connections()

        customer = Customer.objects.create(

            full_name=full_name,
            username=username,
            phone=phone,
            email=email,
            address=address,
            mac_id=original_mac,
            plan=plan_name,
            expiry_date=expiry_date,
            lco=mapping.lco,
            isp=mapping.isp,
        )

        print(
            f"🆕 Created customer after retry: "
            f"{customer.username}"
        )

        return "created"