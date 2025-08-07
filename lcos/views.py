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

class LCORetrieveUpdateDeleteView(TrackCreatedUpdatedUserMixin,generics.RetrieveUpdateDestroyAPIView):
    queryset = LCO.objects.all()
    serializer_class = LCOSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]


from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from accounts.models import User
from .models import LCO
from network.models import OLT
from django.db import IntegrityError
import pandas as pd
import random
import string

class BulkLCOUpload(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    HEADER_ALIASES = {
        "name": ["name", "lco name", "Name"],
        "email": ["email", "Email"],
        "aadhaar_number": [
        "aadhaar", "aadhaar number", "Aadhaar Number","Aadhar",
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
        "olt_uids": ["olt uids", "OLT UIDs", "olts","OLT"],  # comma-separated list
        "lco_name": ["lco", "lco name", "lco_name", "LCO", "LCO Name"]
    }

    def normalize_headers(self, df):
        header_map = {}
        lower_cols = [col.lower().strip() for col in df.columns]

        for field, aliases in self.HEADER_ALIASES.items():
            for alias in aliases:
                if alias.lower() in lower_cols:
                    original_col = df.columns[lower_cols.index(alias.lower())]
                    header_map[field] = original_col
                    break
        return header_map

    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file uploaded'}, status=400)

        try:
            df = pd.read_excel(file)
            header_map = self.normalize_headers(df)

            success_count = 0
            errors = []

            for index, row in df.iterrows():
                try:
                    # Extract and normalize values
                    name = row.get(header_map['name'])
                    email = row.get(header_map['email'])
                    aadhaar_number = str(row.get(header_map['aadhaar_number']))
                    phone = str(row.get(header_map['phone'])).split('.')[0]
                    address = row.get(header_map['address'])
                    olt_uids_str = row.get(header_map['olt_uids'])

                    if not email:
                        errors.append(f"Row {index+1}: Missing email")
                        continue

                    password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

                    # Create user
                    try:
                        user = User.objects.create_user(
                            username=email,
                            email=email,
                            password=password,
                            phone=phone,
                            is_lco=True
                        )
                    except IntegrityError:
                        errors.append(f"Row {index+1}: User with email {email} already exists")
                        continue

                    # Create LCO
                    lco = LCO.objects.create(
                        user=user,
                        name=name,
                        address=address,
                        aadhaar_number=aadhaar_number,
                        phone=phone,
                        created_by=request.user,
                        updated_by=request.user
                    )

                    # Assign OLTs
                    if olt_uids_str:
                        olt_uids = [uid.strip() for uid in str(olt_uids_str).split(',') if uid.strip()]
                        for uid in olt_uids:
                            try:
                                olt = OLT.objects.get(uid=uid, lco__isnull=True)
                                olt.lco = lco
                                olt.save()
                            except OLT.DoesNotExist:
                                errors.append(f"Row {index+1}: OLT with UID '{uid}' not found or already assigned")

                    # Send email
                    try:
                        send_mail(
                            subject="LCO Account Created",
                            message=f"Username: {email}\nPassword: {password}",
                            from_email=settings.EMAIL_HOST_USER,
                            recipient_list=[email],
                            fail_silently=True
                        )
                    except:
                        errors.append(f"Row {index+1}: Email send failed for {email}")

                    success_count += 1

                except Exception as e:
                    errors.append(f"Row {index+1}: {str(e)}")

            if success_count == 0:
                return Response({
                    "message": "No LCOs were uploaded.",
                    "errors": errors
                }, status=400)

            return Response({
                "message": f"{success_count} LCO(s) uploaded successfully.",
                "errors": errors
            }, status=201)


        except Exception as e:
            return Response({'error': str(e)}, status=500)

