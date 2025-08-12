from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import LCO
from .serializers import LCOSerializer
from shared.permissions import IsSuperAdmin
from shared.paginations import StandardResultsSetPagination
from shared.mixins import TrackCreatedUpdatedUserMixin



class LCOCreateListView(TrackCreatedUpdatedUserMixin,generics.ListCreateAPIView):
    queryset = LCO.objects.all()
    serializer_class = LCOSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    pagination_class = StandardResultsSetPagination

from rest_framework.response import Response
from rest_framework import status

class LCORetrieveUpdateDeleteView(
    TrackCreatedUpdatedUserMixin,
    generics.RetrieveUpdateDestroyAPIView
):
    queryset = LCO.objects.all()
    serializer_class = LCOSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def update(self, request, *args, **kwargs):
        try:
            return super().update(request, *args, **kwargs)
        except Exception as e:
            import traceback
            print("UPDATE ERROR:", str(e))
            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction, IntegrityError
import pandas as pd
import random
import string

from accounts.models import User
from .models import LCO
from network.models import OLT

from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from accounts.models import User
from .models import LCO
from network.models import OLT
import pandas as pd
import random
import string

class BulkLCOUpload(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    HEADER_ALIASES = {
        "name": ["name", "lco name", "Name "],
        "email": ["email", "Email"],
        "aadhaar_number": [
            "aadhaar", "aadhaar number", "Aadhaar Number", "Aadhar",
            "aadhar", "aadhar number", "Aadhar Number"
        ],
        "phone": ["phone", "mobile", "Phone"],
        "address": [
            "address", "Address", "addr", "Addr", "ADDR", "ADDRESS",
            "residential address", "Residential Address",
            "home address", "Home Address",
            "full address", "Full Address",
            "current address", "Current Address",
            "present address", "Present Address",
            "house address", "House Address",
            "location", "Location",
            "address line", "Address Line", "addressline", "AddressLine",
            "street address", "Street Address",
            "addr_line", "addr_line1", "addr_line2", "address1", "address2",
            "line1", "line2", "Line 1", "Line 2",
            "house no", "House No", "house number", "House Number",
            "place", "Place", "village", "Village", "town", "Town",
            "building", "Building", "road", "Road", "area", "Area",
        ],
        "olt_uids": ["olt uids", "OLT UIDs", "olts", "OLT", "olt names", "OLT Names"],
        "lco_name": ["lco", "lco name", "lco_name", "LCO", "LCO Name"],
        "networking_name": ["networking name", "Networking Name", "network name", "Network Name"],
    }

    def normalize_headers(self, df):
        header_map = {}
        lower_cols = [col.lower().strip() for col in df.columns]
        for field, aliases in self.HEADER_ALIASES.items():
            for alias in aliases:
                alias_lower = alias.lower().strip()
                if alias_lower in lower_cols:
                    original_col = df.columns[lower_cols.index(alias_lower)]
                    header_map[field] = original_col
                    break
        return header_map

    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file uploaded'}, status=400)

        try:
            df = pd.read_excel(file, skiprows=2)
            header_map = self.normalize_headers(df)

            success_count = 0
            update_count = 0
            errors = []

            # Fetch last unique_id number to start incrementing from
            last_obj = LCO.objects.order_by('-id').first()
            if last_obj and last_obj.unique_id:
                try:
                    last_number = int(last_obj.unique_id.replace("LCO", ""))
                except ValueError:
                    last_number = 0
            else:
                last_number = 0

            current_unique_number = last_number + 1

            for index, row in df.iterrows():
                try:
                    with transaction.atomic():
                        name = row.get(header_map.get('name', ''))
                        email = row.get(header_map.get('email', ''))
                        aadhaar_number = str(row.get(header_map.get('aadhaar_number', '')) or "").strip()
                        phone = str(row.get(header_map.get('phone', '')) or "").split('.')[0]
                        address = row.get(header_map.get('address', ''))
                        olt_uids_str = row.get(header_map.get('olt_uids', ''))
                        networking_name = row.get(header_map.get('networking_name')) if 'networking_name' in header_map else None

                        if not email:
                            errors.append(f"Row {index + 2}: Missing email")
                            continue

                        # Check Aadhaar uniqueness (if given)
                        if aadhaar_number:
                            existing_aadhaar_lco = LCO.objects.filter(aadhaar_number=aadhaar_number).first()
                            if existing_aadhaar_lco:
                                # If LCO exists with this Aadhaar but different user, skip with error
                                if not existing_aadhaar_lco.user.email == email:
                                    errors.append(f"Row {index + 2}: Aadhaar number {aadhaar_number} already exists for another LCO.")
                                    continue

                        print(f"Row {index+2} - name: {name}, address: {address}, aadhaar: {aadhaar_number}, phone: {phone}, networking_name: {networking_name}")

                        user = User.objects.filter(email=email).first()

                        if user:
                            user.username = email
                            user.phone = phone
                            user.is_lco = True
                            user.save()
                            user_updated = True
                        else:
                            password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                            user = User.objects.create_user(
                                username=email,
                                email=email,
                                password=password,
                                phone=phone,
                                is_lco=True
                            )
                            try:
                                send_mail(
                                    subject="LCO Account Created",
                                    message=f"Username: {email}\nPassword: {password}",
                                    from_email=settings.EMAIL_HOST_USER,
                                    recipient_list=[email],
                                    fail_silently=True
                                )
                            except Exception:
                                errors.append(f"Row {index + 2}: Email send failed for {email}")
                            user_updated = False

                        lco = LCO.objects.filter(user=user).first()

                        if not lco:
                            unique_id = f"LCO{current_unique_number:03d}"
                            current_unique_number += 1

                            lco = LCO.objects.create(
                                user=user,
                                name=name,
                                address=address,
                                aadhaar_number=aadhaar_number or None,
                                phone=phone,
                                unique_id=unique_id,
                                created_by=request.user,
                                updated_by=request.user,
                                networking_name=networking_name
                            )
                            lco_updated = False
                        else:
                            lco.name = name
                            lco.address = address
                            lco.aadhaar_number = aadhaar_number or lco.aadhaar_number
                            lco.phone = phone
                            lco.networking_name = networking_name
                            lco.updated_by = request.user
                            lco.save()
                            lco_updated = True

                        # Assign OLTs to LCO
                        if olt_uids_str:
                            olt_inputs = [x.strip() for x in str(olt_uids_str).split(',') if x.strip()]
                            for olt_val in olt_inputs:
                                try:
                                    try:
                                        olt = OLT.objects.get(uid=olt_val, lco__isnull=True)
                                    except OLT.DoesNotExist:
                                        olt = OLT.objects.get(name__iexact=olt_val.strip(), lco__isnull=True)

                                    olt.lco = lco
                                    olt.save()
                                except OLT.DoesNotExist:
                                    errors.append(f"Row {index + 2}: OLT '{olt_val}' not found or already assigned")

                        if lco_updated:
                            update_count += 1
                        else:
                            success_count += 1

                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")

            return Response({
                "message": f"{success_count} LCO(s) created, {update_count} updated.",
                "errors": errors
            }, status=200)

        except Exception as e:
            return Response({'error': str(e)}, status=500)
