# customers/views.py
from rest_framework import generics, filters
from .models import Customer
from .serializers import CustomerSerializer
from rest_framework.pagination import PageNumberPagination
from shared.permissions import IsSuperAdmin,IsLCO
from rest_framework.permissions import IsAuthenticated
from shared.paginations import StandardResultsSetPagination


class CustomerPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'

# customers/views.py
from rest_framework.response import Response
from rest_framework import status

class CustomerListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    queryset = Customer.objects.all().order_by('-last_updated')
    serializer_class = CustomerSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['full_name', 'phone']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print("Validation error:", serializer.errors)  # Add this
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer



#  BULK UPLOAD

import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Customer
from lcos.models import LCO
from network.models import OLT, ISP
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.parsers import MultiPartParser, FormParser

class BulkCustomerUpload(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated, IsSuperAdmin]


    # Mapping of multiple header aliases to model fields
    HEADER_ALIASES = {
        "full_name": ["full name", "name", "customer name"],
        "phone": ["phone", "mobile", "contact number"],
        "email": ["email", "e-mail", "mail"],
        "address": ["address", "residence"],
        "mac_id": ["mac", "mac id", "macid"],
        "plan": ["plan", "internet plan"],
        "lco_ref": ["lco code", "lco_ref"],
        "isp": ["isp id", "isp"],
        "olt": ["olt id", "olt"],
        "v_lan": ["vlan", "v lan", "v_lan"],
        "ont_number": ["ont number", "ont", "ont no"],
        "expiry_date": ["expiry", "expiry date"],
        "signal": ["signal"],
        "kseb_post": ["kseb post", "post"],
        "port": ["port"],
        "distance": ["distance"]
    }

    def normalize_headers(self, df):
        """ Map Excel headers to model fields dynamically """
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
                data = {}

                for field, excel_col in header_map.items():
                    data[field] = row.get(excel_col)

                try:
                    # Foreign key lookups
                    data['isp'] = ISP.objects.get(pk=int(data['isp'])) if data.get('isp') else None
                except:
                    data['isp'] = None

                try:
                    data['olt'] = OLT.objects.get(pk=int(data['olt'])) if data.get('olt') else None
                except:
                    data['olt'] = None

                try:
                    data['lco'] = LCO.objects.get(lco_ref=data['lco_ref']) if data.get('lco_ref') else None
                except:
                    data['lco'] = None

                try:
                    Customer.objects.create(**data)
                    success_count += 1
                except Exception as e:
                    errors.append(f"Row {index+1}: {str(e)}")

            return Response({
                "message": f"{success_count} customers uploaded successfully",
                "errors": errors
            }, status=200)

        except Exception as e:
            return Response({'error': str(e)}, status=500)





# -------------------REPORT MODULE---------------------


from rest_framework.views import APIView
from rest_framework.response import Response
from .models import LCO,ISP
from .serializers import LCODropdownSerializer,ISPDropdownSerializer

class LCOByOLTView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request, olt_id):
        lcos = LCO.objects.filter(olts__id=olt_id)
        serializer = LCODropdownSerializer(lcos, many=True)
        return Response(serializer.data)


class ISPByLCOView(APIView):
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



class CustomerSearchListView(generics.ListAPIView):
    queryset = Customer.objects.all().order_by('-last_updated')
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    pagination_class = CustomerPagination
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

class CustomerReportView(APIView):
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
