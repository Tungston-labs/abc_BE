from django.core.management.base import BaseCommand

from customers.management.commands.whatsapp import (
    send_whatsapp_message,
    send_whatsapp_document
)


class Command(BaseCommand):

    help = "Test WhatsApp PDF sending"

    def handle(self, *args, **kwargs):

        phone = "917025220037"   # YOUR NUMBER

        # Step 1: Send existing template
        template_result = send_whatsapp_message(
            phone=phone,
            lco_name="Test LCO",
            date_str="23 Jun 2026",
            customer_list="Please see attached report."
        )

        print("TEMPLATE RESULT:")
        print(template_result)
        print("PDF URL:", pdf_url)
        print("PDF PATH:", pdf_path)
        print("FILE EXISTS:", pdf_path.exists())

        # Step 2: Send PDF
        document_result = send_whatsapp_document(
            phone=phone,
            document_url="https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
            filename="Expiry_Report_Test.pdf"
        )

        print("DOCUMENT RESULT:")
        print(document_result)