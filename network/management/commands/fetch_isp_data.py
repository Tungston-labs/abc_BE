from django.core.management.base import BaseCommand
from lcos.models import LCOISPMapping
from network.services.isp_handler import fetch_isp_data


class Command(BaseCommand):
    help = "Fetch ISP Data"

    def handle(self, *args, **kwargs):

        mappings = LCOISPMapping.objects.filter(is_active=True)

        for mapping in mappings:
            try:
                data = fetch_isp_data(mapping)

                print(f"Success: {mapping.partner_name}")
                print(data)

                # 👉 NEXT STEP: Save this data

            except Exception as e:
                print(f"Error for {mapping.partner_name}: {e}")