
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
        print("⏭ Skipped: API record has no username")
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

    full_name = clean_value(
        item.get("full_name")
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

    # ========================================================
    # FIND CUSTOMER BY USERNAME ONLY
    # ========================================================

    customer = get_customer_by_username(
        username
    )

    # ========================================================
    # CREATE NEW CUSTOMER
    # ========================================================

    if not customer:

        customer = Customer(
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