# customers/views.py
from rest_framework import generics, filters
from .models import Customer
from .serializers import CustomerSerializer
from rest_framework.pagination import PageNumberPagination
from shared.permissions import IsSuperAdmin,IsLCO
from rest_framework.permissions import IsAuthenticated
from shared.paginations import StandardResultsSetPagination
import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Customer
from lcos.models import LCO
from network.models import OLT, ISP
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.parsers import MultiPartParser, FormParser
from shared.mixins import TrackCreatedUpdatedUserMixin

import logging

logger = logging.getLogger(__name__)
class CustomerPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'


from rest_framework.response import Response

class CustomerListCreateView(TrackCreatedUpdatedUserMixin, generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CustomerSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['full_name', 'phone','username','ont_number']

    def get_search_fields(self, view, request):
        # Return all Customer model field names dynamically
        return [field.name for field in Customer._meta.get_fields() 
                if hasattr(field, "attname")]


    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Customer.objects.all().order_by('-last_updated')
        if hasattr(user, 'lco_profile'):
            lco = user.lco_profile
            return Customer.objects.filter(lco=lco).order_by('-last_updated')
        return Customer.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'lco_profile') and not user.is_super_admin:
            serializer.save(lco=user.lco_profile)
        else:
            serializer.save()

    # ✅ Add this method
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_data = self.get_paginated_response(serializer.data).data
            # ✅ Inject user role
            paginated_data['is_super_admin'] = request.user.is_super_admin
            return Response(paginated_data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "results": serializer.data,
            "is_super_admin": request.user.is_super_admin
        })



import requests
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Customer
from .serializers import CustomerSerializer


import requests
from django.conf import settings
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class CustomerRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CustomerSerializer

    def get_queryset(self):
        user = self.request.user

        if user.is_super_admin:
            return Customer.objects.all()
        elif hasattr(user, 'lco_profile'):
            return Customer.objects.filter(lco=user.lco_profile)

        return Customer.objects.none()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        print("ONT Number:", instance.ont_number)
        logger.error("========== RETRIEVE HIT ==========")
        logger.error(f"ONT NUMBER: {instance.ont_number}")

        serial_number = instance.ont_number

        if serial_number:
            try:
                base_url = settings.SIGNAL_API_BASE_URL
                url = f"{base_url}/signal/{serial_number}"

                print("Calling URL:", url)

                response = requests.get(url, timeout=3)

                print("Status Code:", response.status_code)
                print("Response Text:", response.text)

                if response.status_code == 200:
                    data = response.json()

                    print("API Data:", data)

                    rx_power = data.get("rx_power")
                    print("RX Power:", rx_power)

                    if rx_power is not None:
                        instance.signal = str(rx_power)
                        instance.save()

                        print("Saved Signal:", instance.signal)

            except Exception as e:
                print("Signal API error:", str(e))

        serializer = self.get_serializer(instance)
        return Response(serializer.data)







class DropdownDataAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        lco_id = request.query_params.get("lco_id", None)

        # ==========================================
        # SUPER ADMIN
        # ==========================================
        if user.is_super_admin:

            lcos = LCO.objects.all()

            lco_data = [
                {
                    "id": lco.id,
                    "label": f"{lco.name} ({lco.address})"
                }
                for lco in lcos
            ]

        # ==========================================
        # LCO USER
        # ==========================================
        elif hasattr(user, 'lco_profile'):

            lco = user.lco_profile

            lco_data = [
                {
                    "id": lco.id,
                    "label": f"{lco.name} ({lco.address})"
                }
            ]

            # Automatically use logged-in LCO id
            lco_id = lco.id

        else:

            return Response(
                {"error": "Invalid user"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ==========================================
        # ISP LIST
        # ==========================================
        isps = ISP.objects.all()

        isp_data = [
            {
                "id": isp.id,
                "name": isp.name
            }
            for isp in isps
        ]

        # ==========================================
        # OLT LIST
        # ==========================================
        if lco_id:

            olts = OLT.objects.filter(
                lco_id=lco_id
            )

        else:

            olts = OLT.objects.none()

        olt_data = [
            {
                "id": olt.id,
                "name": olt.name
            }
            for olt in olts
        ]

        # ==========================================
        # LCO REF
        # ==========================================
        lco_ref = None

        if lco_id:

            try:

                lco = LCO.objects.get(id=lco_id)

                lco_ref = lco.user.username

            except LCO.DoesNotExist:

                return Response(
                    {"error": "LCO not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

        return Response({

            "lcos": lco_data,

            "isps": isp_data,

            "olts": olt_data,

            "lco_ref": lco_ref
        })

from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Customer, ISP, OLT, LCO
from shared.mixins import TrackCreatedUpdatedUserMixin
from shared.permissions import IsSuperAdmin  # Make sure you import this

# customers/views.py
import pandas as pd
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Customer
from network.models import OLT, ISP
from lcos.models import LCO
from shared.mixins import TrackCreatedUpdatedUserMixin
from shared.permissions import IsSuperAdmin
import pandas as pd
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
import traceback
import pandas as pd
import traceback
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from customers.models import Customer
from lcos.models import LCO
from network.models import ISP, OLT
from django.db.models.signals import post_save
from shared.signals import log_create_or_update


class BulkCustomerUpload(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    HEADER_ALIASES = {
        "full_name": ["Customer", "name", "Customer Name", "Name,", "Full Name", "FULL_NAME"],
        "phone": ["phone", "mobile", "contact number", "Mobile", "Mobile No.", "Phone", "MOBILE", "PHONE"],
        "email": ["email", "e-mail", "mail", "EMAIL_ID", "Email Address", "Email", "EMAIL ID"],
        "address": ["address", "residence", "Address", "ADDRESS", "Permanent Address"],
        "mac_id": ["mac", "mac id", "macid", "MACID", "MAC_ID"],
        "plan": ["plan", "internet plan", "Plan", "Plan Name"],
        "lco": ["lco", "LCO", "lco code", "LCO_CODE"],
        "lco_ref": ["lco_ref", "LCO_REF", "lco reference", "LCO Reference"],
        "isp": ["isp id", "isp", "ISP"],
        "olt": ["olt id", "olt", "OLT IP", "OLT Name", "OLT"],
        "v_lan": ["vlan", "v lan", "v_lan", "V_LAN"],
        "ont_number": ["ont number", "ont", "ont no", "ONT_NUMBER"],
        "expiry_date": ["expiry", "expiry date", "Expiry Date", "Validity End", "EXPIRY_DATE"],
        "signal": ["signal", "SIGNAL"],
        "kseb_post": ["kseb post", "post", "KSEB_POST"],
        "port": ["port", "PORT"],
        "distance": ["distance", "DISTANCE"],
        "username": ["username", "user name", "login name", "customer username", "USERNAME"],
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

        print(" HEADER MAP:", header_map)
        return header_map

    def post(self, request):
        file = request.FILES.get('file')
        request_isp_id = request.data.get("isp")
        request_lco_id = request.data.get("lco")

        # ---------------- VALIDATION ----------------
        if not file:
            return Response({"error": "No file uploaded"}, status=400)

        if not request_isp_id and not request_lco_id:
            return Response({"error": "Select ISP or LCO"}, status=400)

        if request_isp_id and request_lco_id:
            return Response({"error": "Select either ISP or LCO"}, status=400)

        # ---------------- PRELOAD ----------------
        selected_isp = None
        selected_lco = None

        if request_isp_id:
            try:
                selected_isp = ISP.objects.get(pk=request_isp_id)
            except ISP.DoesNotExist:
                return Response({"error": "Invalid ISP"}, status=400)

        if request_lco_id:
            try:
                selected_lco = LCO.objects.get(pk=request_lco_id)
            except LCO.DoesNotExist:
                return Response({"error": "Invalid LCO"}, status=400)

        # ---------------- READ EXCEL ----------------
        try:
            df = pd.read_excel(file)
        except Exception as e:
            return Response({"error": f"Invalid Excel: {str(e)}"}, status=400)

        header_map = self.normalize_headers(df)

        success_count = 0
        created_count = 0
        updated_count = 0
        errors = []
        seen_usernames = set()

        # Cache
        isp_cache = {isp.name.lower(): isp for isp in ISP.objects.all()}
        lco_cache = {lco.lco_code.lower(): lco for lco in LCO.objects.all()}
        olt_cache = {olt.name.lower(): olt for olt in OLT.objects.all()}

        # ✅ DISABLE SIGNALS
        post_save.disconnect(log_create_or_update, sender=Customer)

        try:
            # ✅ SINGLE TRANSACTION (important)
            with transaction.atomic():

                for index, row in df.iterrows():
                    try:
                        data = {}

                        for field, excel_col in header_map.items():
                            val = row.get(excel_col)
                            data[field] = None if pd.isna(val) else val

                        # -------- USERNAME --------
                        username = str(data.get("username", "")).strip().lower()

                        if not username:
                            print(f"❌ SKIPPED Row {index+1}: Missing username")
                            errors.append(f"Row {index+1}: Missing username")
                            continue

                        if username in seen_usernames:
                            print(f"❌ SKIPPED Row {index+1}: Duplicate username in file")
                            errors.append(f"Row {index+1}: Duplicate username in file")
                            continue

                        seen_usernames.add(username)

                        # -------- ONT --------
                        ont_number = data.get("ont_number")
                        if ont_number:
                            ont_number = str(ont_number).strip()

                        # ✅ FIX: Allow update instead of skipping
                        if ont_number:
                            existing_ont = Customer.objects.filter(
                                ont_number=ont_number
                            ).exclude(username=username).first()

                            if existing_ont:
                                print(f"⚠️ ONT reassigned {existing_ont.username} → {username}")
                                existing_ont.username = username
                                existing_ont.save()

                        # -------- DEFAULTS --------
                        defaults = {}

                        text_fields = [
                            "full_name", "email", "address", "plan",
                            "mac_id", "v_lan", "signal", "kseb_post",
                            "port", "lco_ref"
                        ]

                        for field in text_fields:
                            if data.get(field) not in (None, ""):
                                defaults[field] = str(data[field]).strip()

                        # PHONE
                        if data.get("phone"):
                            defaults["phone"] = str(data["phone"]).split('.')[0].strip()

                        # DISTANCE
                        if data.get("distance") not in (None, ""):
                            try:
                                defaults["distance"] = float(data["distance"])
                            except:
                                errors.append(f"Row {index+1}: Invalid distance")

                        # EXPIRY DATE
                        if data.get("expiry_date"):
                            try:
                                defaults["expiry_date"] = pd.to_datetime(
                                    data["expiry_date"], errors="coerce"
                                ).date()
                            except:
                                pass

                        if ont_number:
                            defaults["ont_number"] = ont_number

                        # ISP
                        if selected_isp:
                            defaults["isp"] = selected_isp
                        elif data.get("isp"):
                            isp_name = str(data["isp"]).strip().lower()
                            if isp_name in isp_cache:
                                defaults["isp"] = isp_cache[isp_name]

                        # LCO
                        if selected_lco:
                            defaults["lco"] = selected_lco
                            if hasattr(selected_lco, "isp"):
                                defaults["isp"] = selected_lco.isp
                        elif data.get("lco"):
                            lco_code = str(data["lco"]).strip().lower()
                            if lco_code in lco_cache:
                                defaults["lco"] = lco_cache[lco_code]

                        # OLT
                        if data.get("olt"):
                            olt_val = str(data["olt"]).strip()
                            try:
                                defaults["olt"] = OLT.objects.get(pk=int(olt_val))
                            except:
                                if olt_val.lower() in olt_cache:
                                    defaults["olt"] = olt_cache[olt_val.lower()]

                        # DEBUG
                        print(f"\n📌 Row {index+1}")
                        print("Username:", username)
                        print("Defaults:", defaults)

                        # SAVE
                        obj, created = Customer.objects.update_or_create(
                            username=username,
                            defaults=defaults
                        )

                        if created:
                            created_count += 1
                            print(f"✅ CREATED: {username}")
                        else:
                            updated_count += 1
                            print(f"🔄 UPDATED: {username}")

                        success_count += 1

                    except Exception as e:
                        print("\n🔥 ERROR:")
                        traceback.print_exc()
                        errors.append(f"Row {index+1}: {str(e)}")

        finally:
            # ✅ RE-ENABLE SIGNALS
            post_save.connect(log_create_or_update, sender=Customer)

        return Response({
            "message": f"{success_count} processed",
            "created": created_count,
            "updated": updated_count,
            "errors": errors
        })
# class BulkCustomerUpload(APIView):
#     parser_classes = (MultiPartParser, FormParser)
#     permission_classes = [IsAuthenticated]  # keep your IsSuperAdmin if needed

#     HEADER_ALIASES = {
#         "full_name": ["Customer", "name", "Customer Name", "Name,", "Full Name", "FULL_NAME"],
#         "phone": ["phone", "mobile", "contact number", "Mobile", "Mobile No.", "Phone", "MOBILE", "PHONE"],
#         "email": ["email", "e-mail", "mail", "EMAIL_ID", "Email Address", "Email", "EMAIL ID"],
#         "address": ["address", "residence", "Address", "ADDRESS", "Permanent Address"],
#         "mac_id": ["mac", "mac id", "macid", "MACID", "MAC_ID"],
#         "plan": ["plan", "internet plan", "Plan", "Plan Name"],
#         "lco": ["lco", "LCO", "lco code", "LCO_CODE"],
#         "lco_ref": ["lco_ref", "LCO_REF", "lco reference", "LCO Reference"],
#         "isp": ["isp id", "isp", "ISP"],
#         "olt": ["olt id", "olt", "OLT IP", "OLT Name", "OLT"],
#         "v_lan": ["vlan", "v lan", "v_lan", "V_LAN"],
#         "ont_number": ["ont number", "ont", "ont no", "ONT_NUMBER"],
#         "expiry_date": ["expiry", "expiry date", "Expiry Date", "Validity End", "EXPIRY_DATE"],
#         "signal": ["signal", "SIGNAL"],
#         "kseb_post": ["kseb post", "post", "KSEB_POST"],
#         "port": ["port", "PORT"],
#         "distance": ["distance", "DISTANCE"],
#         "username": ["username", "user name", "login name", "customer username", "USERNAME"],
#     }

#     def options(self, request, *args, **kwargs):
#         return Response(status=200)

#     def normalize_headers(self, df):
#         header_map = {}
#         lower_cols = [col.lower().strip() for col in df.columns]

#         for field, aliases in self.HEADER_ALIASES.items():
#             for alias in aliases:
#                 if alias.lower() in lower_cols:
#                     original_col = df.columns[lower_cols.index(alias.lower())]
#                     header_map[field] = original_col
#                     break
#         return header_map

#     def post(self, request, *args, **kwargs):
#         file = request.FILES.get('file')
#         if not file:
#             return Response({'error': 'No file uploaded'}, status=400)

#         request_isp_id = request.data.get("isp")

#         try:
#             df = pd.read_excel(file)
#         except Exception as e:
#             return Response({'error': f'Invalid Excel file: {str(e)}'}, status=400)

#         header_map = self.normalize_headers(df)

#         success_count = 0
#         errors = []
#         seen_usernames = set()

#         # 🔹 Optional: preload DB data for performance
#         isp_cache = {isp.name.lower(): isp for isp in ISP.objects.all()}
#         olt_cache = {olt.name.lower(): olt for olt in OLT.objects.all()}
#         lco_cache = {lco.lco_code.lower(): lco for lco in LCO.objects.all()}

#         for index, row in df.iterrows():
#             data = {}

#             # ---------------- Map Excel columns ----------------
#             for field, excel_col in header_map.items():
#                 val = row.get(excel_col)
#                 if pd.isna(val):
#                     val = None
#                 data[field] = val

#             # ---------------- Username (UNIQUE KEY) ----------------
#             username = data.get('username')
#             if username:
#                 username = str(username).strip().lower()
#             else:
#                 errors.append(f"Row {index+1}: Missing username")
#                 continue

#             # Duplicate inside Excel
#             if username in seen_usernames:
#                 errors.append(f"Row {index+1}: Duplicate username in file '{username}'")
#                 continue
#             seen_usernames.add(username)

#             # ---------------- Phone cleanup ----------------
#             phone = data.get('phone')
#             if phone:
#                 phone = str(phone).split('.')[0].strip()
#                 if not phone.isdigit():
#                     errors.append(f"Row {index+1}: Invalid phone number")
#                     continue
#                 data['phone'] = phone
#             else:
#                 data['phone'] = None  # allow empty

#             # ---------------- Prepare defaults ----------------
#             defaults = {}

#             for field in [
#                 'full_name', 'email', 'address', 'mac_id', 'plan',
#                 'v_lan', 'ont_number', 'signal', 'kseb_post', 'port', 'distance'
#             ]:
#                 if data.get(field) not in (None, ''):
#                     defaults[field] = data[field]

#             # ---------------- Expiry date ----------------
#             expiry_val = data.get('expiry_date')
#             if expiry_val not in (None, ''):
#                 try:
#                     defaults['expiry_date'] = pd.to_datetime(expiry_val, errors='coerce').date()
#                 except Exception:
#                     defaults['expiry_date'] = None

#             # ---------------- ISP ----------------
#             if request_isp_id:
#                 try:
#                     defaults['isp'] = ISP.objects.get(pk=int(request_isp_id))
#                 except ISP.DoesNotExist:
#                     errors.append(f"Row {index+1}: ISP '{request_isp_id}' not found.")
#             elif data.get('isp'):
#                 isp_name = str(data['isp']).strip().lower()
#                 if isp_name in isp_cache:
#                     defaults['isp'] = isp_cache[isp_name]
#                 else:
#                     errors.append(f"Row {index+1}: ISP '{data['isp']}' not found.")

#             # ---------------- OLT ----------------
#             if data.get('olt'):
#                 olt_val = str(data['olt']).strip()
#                 try:
#                     defaults['olt'] = OLT.objects.get(pk=int(olt_val))
#                 except:
#                     olt_name = olt_val.lower()
#                     if olt_name in olt_cache:
#                         defaults['olt'] = olt_cache[olt_name]
#                     else:
#                         errors.append(f"Row {index+1}: OLT '{olt_val}' not found.")

#             # ---------------- LCO ----------------
#             if data.get('lco'):
#                 lco_code = str(data['lco']).strip().lower()
#                 if lco_code in lco_cache:
#                     defaults['lco'] = lco_cache[lco_code]
#                 else:
#                     errors.append(f"Row {index+1}: LCO '{data['lco']}' not found.")

#             # ---------------- LCO_REF ----------------
#             if data.get('lco_ref'):
#                 defaults['lco_ref'] = str(data['lco_ref']).strip()

#             # ---------------- Save ----------------
#             try:
#                 with transaction.atomic():
#                     Customer.objects.update_or_create(
#                         username=username,
#                         defaults={
#                             **defaults,
#                             "phone": data.get("phone")
#                         }
#                     )
#                     success_count += 1
#             except Exception as e:
#                 errors.append(f"Row {index+1}: {str(e)}")

#         return Response({
#             "message": f"{success_count} customers uploaded/updated successfully",
#             "errors": errors
#         }, status=200)


# -------------------REPORT MODULE---------------------


from rest_framework.views import APIView
from rest_framework.response import Response
from .models import LCO,ISP
from .serializers import LCODropdownSerializer,ISPDropdownSerializer

class LCOByOLTView(TrackCreatedUpdatedUserMixin,APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request, olt_id):
        lcos = LCO.objects.filter(olts__id=olt_id)
        serializer = LCODropdownSerializer(lcos, many=True)
        return Response(serializer.data)


class ISPByLCOView(TrackCreatedUpdatedUserMixin,APIView):
    def get(self, request, lco_id):
        isps = ISP.objects.filter(lco__id=lco_id)
        serializer = ISPDropdownSerializer(isps, many=True)
        return Response(serializer.data)


# customers/views.py
from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from shared.paginations import CustomerScrollPagination
from .serializers import CustomerSerializer
from .models import Customer

class CustomerSearchListView(generics.ListAPIView):
    queryset = Customer.objects.all().order_by('-last_updated')
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = [
        'full_name', 'phone', 'email', 'mac_id', 'ont_number', 'address',
        'v_lan', 'kseb_post', 'port', 'plan'
    ]
    filterset_fields = {
        'lco': ['exact'],
        'olt': ['exact'],
        'isp': ['exact'],
    }

    pagination_class = CustomerScrollPagination



from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from openpyxl import Workbook
from io import BytesIO
from .models import Customer
from datetime import datetime
from django.db.models import Q


class CustomerReportView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = None

    FIELD_MAP = {
        "olt_name": "olt__name",
        "isp_name": "isp__name",
        "lco_name": "lco__name",
    }

    def post(self, request):
        selected_fields = request.data.get("fields", [])
        mandatory_fields = ["full_name", "address", "phone"]
        all_fields = list(set(mandatory_fields + selected_fields))

        valid_fields = [f.name for f in Customer._meta.fields]
        for field in all_fields:
            if field not in valid_fields and field not in self.FIELD_MAP:
                return Response({"error": f"Invalid field: {field}"}, status=400)

        # Filters
        filters = request.data.get("filters", {})
        filters = {k: v for k, v in filters.items() if v not in [None, ""]}

        # Search term
        search_term = request.data.get("search", "").strip()

        # Build queryset
        queryset = Customer.objects.all()

        if filters:
            queryset = queryset.filter(**filters)

        if search_term:
            queryset = queryset.filter(
                Q(full_name__icontains=search_term)
                | Q(phone__icontains=search_term)
                | Q(address__icontains=search_term)
                | Q(username__icontains=search_term)
            )

        # ORM field resolution
        resolved_fields = [self.FIELD_MAP.get(f, f) for f in all_fields]

        queryset = queryset.values(*resolved_fields).iterator(chunk_size=2000)

        # Excel generation
        wb = Workbook(write_only=True)
        ws = wb.create_sheet(title="Customers")
        ws.append(all_fields)

        for customer in queryset:
            row = []
            for field in all_fields:
                value = customer.get(self.FIELD_MAP.get(field, field), "")
                if isinstance(value, datetime) and value.tzinfo is not None:
                    value = value.replace(tzinfo=None)
                row.append(value)
            ws.append(row)

        virtual_workbook = BytesIO()
        wb.save(virtual_workbook)
        virtual_workbook.seek(0)

        response = HttpResponse(
            virtual_workbook.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="customer_report.xlsx"'
        return response


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from customers.models import Customer
from lcos.models import LCO
from network.models import OLT, ISP,Switch
from tickets.models import Ticket


class DashboardCountsView(APIView):
    permission_classes = [IsAuthenticated]  # Optional: Use if auth is required

    def get(self, request):
        today = timezone.now().date()
        five_days_from_now = today + timedelta(days=5)

        data = {
            "total_customers": Customer.objects.count(),
            "expired_plan_customers": Customer.objects.filter(
            expiry_date__range=(today, five_days_from_now)
        ).order_by('expiry_date').count(),
            "total_lcos": LCO.objects.count(),
            "total_olts": OLT.objects.count(),
            "total_isps": ISP.objects.count(),
            "total_switches":Switch.objects.count(), 
            "total_tickets": Ticket.objects.filter(status="open").count(),

        }

        return Response(data)







# LCO VIEW FOR LISTING CUSTMERS UNDER THAT LCO

class LCOCustomerSearchListView(generics.ListAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, IsLCO]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = [
        'full_name', 'phone', 'email', 'mac_id', 'ont_number', 'address',
        'v_lan', 'kseb_post', 'port', 'plan'
    ]
    filterset_fields = ['olt', 'isp']  

    def get_queryset(self):
        return Customer.objects.filter(lco__user=self.request.user).order_by('-last_updated')

from datetime import timedelta



class CustomersExpiringSoonFilteredView(generics.ListAPIView):

    permission_classes = [IsAuthenticated]

    serializer_class = CustomerSerializer

    pagination_class = StandardResultsSetPagination

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter
    ]

    search_fields = [
        "full_name",
        "phone",
        "plan",
        "username"
    ]

    def get_queryset(self):

        user = self.request.user

        queryset = Customer.objects.all().order_by(
            "expiry_date"
        )

        # -----------------------------
        # Query Params
        # -----------------------------
        lco = self.request.GET.get("lco")
        isp = self.request.GET.get("isp")

        from_date = self.request.GET.get(
            "from_date"
        )

        to_date = self.request.GET.get(
            "to_date"
        )

        # -----------------------------
        # Default Expiring in 5 days
        # -----------------------------
        if not from_date and not to_date:

            today = timezone.now().date()

            five_days_from_now = (
                today + timedelta(days=5)
            )

            queryset = queryset.filter(
                expiry_date__range=(
                    today,
                    five_days_from_now
                )
            )

        # -----------------------------
        # Custom Date Range
        # -----------------------------
        if from_date and to_date:

            queryset = queryset.filter(
                expiry_date__range=[
                    from_date,
                    to_date
                ]
            )

        elif from_date:

            queryset = queryset.filter(
                expiry_date__gte=from_date
            )

        elif to_date:

            queryset = queryset.filter(
                expiry_date__lte=to_date
            )

        # -----------------------------
        # LCO Filter
        # -----------------------------
        if lco:

            queryset = queryset.filter(
                lco_id=lco
            )

        # -----------------------------
        # ISP Filter
        # -----------------------------
        if isp:

            queryset = queryset.filter(
                isp_id=isp
            )

        # -----------------------------
        # Super Admin
        # -----------------------------
        if user.is_super_admin:

            return queryset

        # -----------------------------
        # LCO User
        # -----------------------------
        if hasattr(user, "lco_profile"):

            return queryset.filter(
                lco=user.lco_profile
            )

        return Customer.objects.none()

    def list(self, request, *args, **kwargs):

        response = super().list(
            request,
            *args,
            **kwargs
        )

        response.data["is_super_admin"] = (
            request.user.is_super_admin
        )

        return response


from rest_framework.permissions import AllowAny


class CustomerSignalListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        limit = int(request.query_params.get("limit", 5000))  # default 5k
        offset = int(request.query_params.get("offset", 0))

        queryset = Customer.objects.exclude(ont_number__isnull=True)\
                                   .exclude(ont_number="")\
                                   .values("id", "ont_number", "signal")[offset:offset+limit]

        return Response({
            "count": Customer.objects.count(),
            "limit": limit,
            "offset": offset,
            "results": list(queryset)
        })