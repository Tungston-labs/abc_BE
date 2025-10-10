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


class CustomerPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'


from rest_framework.response import Response

class CustomerListCreateView(TrackCreatedUpdatedUserMixin, generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CustomerSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['full_name', 'phone','username']

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



class CustomerRetrieveUpdateDestroyView(TrackCreatedUpdatedUserMixin, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CustomerSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Customer.objects.all()
        elif hasattr(user, 'lco_profile'):
            return Customer.objects.filter(lco=user.lco_profile)
        return Customer.objects.none()




# drop down data of lco,olt,isp

class DropdownDataAPIView(APIView):
    def get(self, request):
        lco_id = request.query_params.get("lco_id", None)

        # LCO list with name and address
        lcos = LCO.objects.all()
        lco_data = [
            {
                "id": lco.id,
                "label": f"{lco.name} ({lco.address})"
            } for lco in lcos
        ]

        # ISP list
        isps = ISP.objects.all()
        isp_data = [
            {
                "id": isp.id,
                "name": isp.name
            } for isp in isps
        ]

        # Filtered OLTs based on selected LCO
        if lco_id:
            olts = OLT.objects.filter(lco_id=lco_id)
        else:
            olts = OLT.objects.none()

        olt_data = [
            {
                "id": olt.id,
                "name": olt.name
            } for olt in olts
        ]

        # LCO ref (e.g., username of linked user)
        lco_ref = None
        if lco_id:
            try:
                lco = LCO.objects.get(id=lco_id)
                lco_ref = lco.user.username
            except LCO.DoesNotExist:
                return Response({"error": "LCO not found"}, status=status.HTTP_404_NOT_FOUND)

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

class BulkCustomerUpload(TrackCreatedUpdatedUserMixin, APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    HEADER_ALIASES = {
        "full_name": ["Customer", "name", "Customer Name", "Name,", "Full Name", "FULL_NAME"],
        "phone": ["phone", "mobile", "contact number", "Mobile", "Mobile No.", "Phone", "MOBILE", "PHONE"],
        "email": ["email", "e-mail", "mail", "EMAIL_ID", "Email Address", "Email", "EMAIL ID"],
        "address": ["address", "residence", "Address", "ADDRESS", "Permanent Address"],
        "mac_id": ["mac", "mac id", "macid", "MACID", "MAC_ID"],
        "plan": ["plan", "internet plan", "Plan", "Plan Name"],
        "lco_ref": ["lco code", "lco_ref", "LCO_REF"],
        "lco": ["lco", "LCO Code"],
        "isp": ["isp id", "isp", "ISP"],
        "olt": ["olt id", "olt", "OLT IP", "OLT Name", "OLT"],
        "v_lan": ["vlan", "v lan", "v_lan", "V_LAN"],
        "ont_number": ["ont number", "ont", "ont no", "ONT_NUMBER"],
        "expiry_date": ["expiry", "expiry date", "Expiry Date", "Validity End", "Expiry date", "EXPIRY_DATE"],
        "signal": ["signal", "SIGNAL"],
        "kseb_post": ["kseb post", "post", "KSEB_POST"],
        "port": ["port", "PORT"],
        "distance": ["distance", "DISTANCE"],
        "username": ["username", "user name", "login name", "customer username", "USERNAME"],
    }

    def normalize_headers(self, df):
        """Map Excel headers to model fields based on aliases"""
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

        request_isp_id = request.data.get("isp")

        try:
            df = pd.read_excel(file)
            header_map = self.normalize_headers(df)

            success_count = 0
            errors = []

            for index, row in df.iterrows():
                data = {}

                # Map Excel data to internal fields
                for field, excel_col in header_map.items():
                    data[field] = row.get(excel_col)

                # ---------------- Date conversion ----------------
                expiry_val = data.get('expiry_date')
                if pd.notna(expiry_val):
                    try:
                        if isinstance(expiry_val, (int, float)):
                            # Excel serial number
                            data['expiry_date'] = pd.to_datetime(expiry_val, unit='d', origin='1899-12-30').date()
                        else:
                            data['expiry_date'] = pd.to_datetime(str(expiry_val)).date()
                    except Exception:
                        data['expiry_date'] = None
                else:
                    data['expiry_date'] = None

                # ---------------- Phone cleanup ----------------
                phone = data.get('phone')
                if phone:
                    data['phone'] = str(phone).split('.')[0].strip()

                # ---------------- ISP ----------------
                isp_val = data.get('isp')
                try:
                    if request_isp_id:
                        data['isp'] = ISP.objects.get(pk=int(request_isp_id))
                    elif isp_val:
                        try:
                            data['isp'] = ISP.objects.get(pk=int(isp_val))
                        except (ValueError, ISP.DoesNotExist):
                            data['isp'] = ISP.objects.get(name__iexact=str(isp_val).strip())
                    else:
                        data['isp'] = None
                except ISP.DoesNotExist:
                    errors.append(f"Row {index+1}: ISP '{isp_val}' not found.")
                    data['isp'] = None

                # ---------------- OLT ----------------
                olt_val = data.get('olt')
                try:
                    if olt_val:
                        try:
                            data['olt'] = OLT.objects.get(pk=int(olt_val))
                        except (ValueError, OLT.DoesNotExist):
                            data['olt'] = OLT.objects.get(name__iexact=str(olt_val).strip())
                    else:
                        data['olt'] = None
                except OLT.DoesNotExist:
                    errors.append(f"Row {index+1}: OLT '{olt_val}' not found.")
                    data['olt'] = None

                # ---------------- LCO ----------------
                lco_ref_val = data.get('lco_ref')
                try:
                    if lco_ref_val:
                        try:
                            data['lco'] = LCO.objects.get(lco_ref__iexact=str(lco_ref_val).strip())
                        except LCO.DoesNotExist:
                            data['lco'] = LCO.objects.get(name__iexact=str(lco_ref_val).strip())
                    else:
                        data['lco'] = None
                except LCO.DoesNotExist:
                    errors.append(f"Row {index+1}: LCO '{lco_ref_val}' not found.")
                    data['lco'] = None

                # Remove potential conflicting keys for mixin
                data.pop('created_by', None)
                data.pop('updated_by', None)

                # ---------------- Create or Update ----------------
                try:
                    if not data.get('phone'):
                        errors.append(f"Row {index+1}: Missing phone number")
                        continue

                    try:
                        # Update existing customer
                        customer = Customer.objects.get(phone=data['phone'])
                        for field, value in data.items():
                            setattr(customer, field, value)
                        customer.save()  # mixin will handle updated_by and logging
                        print(f"Row {index+1}: Updated customer {data['phone']}")
                    except Customer.DoesNotExist:
                        # Create new customer
                        Customer.objects.create(**data)  # mixin handles created_by, logging
                        print(f"Row {index+1}: Created customer {data['phone']}")

                    success_count += 1
                except Exception as e:
                    errors.append(f"Row {index+1}: {str(e)}")
                    print(f"Row {index+1} Error: {str(e)}")

            return Response({
                "message": f"{success_count} customers uploaded/updated successfully",
                "errors": errors
            }, status=200)

        except Exception as e:
            return Response({'error': str(e)}, status=500)






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


from rest_framework import generics, filters
from .models import Customer
from .serializers import CustomerSerializer
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q



class CustomerSearchListView(TrackCreatedUpdatedUserMixin,generics.ListAPIView):
    queryset = Customer.objects.all().order_by('-last_updated')
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    # pagination_class = CustomerPagination
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = [
        'full_name', 'phone', 'email', 'mac_id', 'ont_number', 'address',
        'v_lan', 'kseb_post', 'port', 'plan'
    ]
    filterset_fields = ['olt', 'lco', 'isp']


import pandas as pd
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Customer

class CustomerReportView(TrackCreatedUpdatedUserMixin,APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        selected_fields = request.data.get('fields', [])

        # Mandatory fields
        mandatory_fields = ['full_name', 'address', 'phone']
        all_fields = list(set(mandatory_fields + selected_fields))

        # Validate field names
        valid_fields = [field.name for field in Customer._meta.fields]
        for field in all_fields:
            if field not in valid_fields:
                return Response({"error": f"Invalid field: {field}"}, status=400)

        # Query and prepare data
        customers = Customer.objects.all().values(*all_fields)
        df = pd.DataFrame(list(customers))

        # Return Excel file
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=customer_report.xlsx'
        df.to_excel(response, index=False)
        return response


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from customers.models import Customer
from lcos.models import LCO
from network.models import OLT, ISP


class DashboardCountsView(APIView):
    permission_classes = [IsAuthenticated]  # Optional: Use if auth is required

    def get(self, request):
        today = timezone.now().date()

        data = {
            "total_customers": Customer.objects.count(),
            "expired_plan_customers": Customer.objects.filter(expiry_date__lt=today).count(),
            "total_lcos": LCO.objects.count(),
            "total_olts": OLT.objects.count(),
            "total_isps": ISP.objects.count(),
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


# customers/views.py

from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from datetime import date, timedelta
from .models import Customer
from .serializers import CustomerSerializer

class CustomersExpiringSoonFilteredView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CustomerSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['lco']
    search_fields = ['full_name', 'phone','plan']

    def get_queryset(self):
        today = timezone.now().date()
        five_days_from_now = today + timedelta(days=5)

        queryset = Customer.objects.filter(
            expiry_date__range=(today, five_days_from_now)
        ).order_by('expiry_date')

        user = self.request.user

        if user.is_super_admin:
            return queryset
        elif hasattr(user, 'lco_profile'):
            return queryset.filter(lco=user.lco_profile)
        return Customer.objects.none()

