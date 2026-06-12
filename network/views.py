from rest_framework import generics,filters
from rest_framework.permissions import IsAuthenticated
from .models import Switch,ISP
from .serializers import SwitchSerializer,ISPSerializer
from shared.permissions import IsSuperAdmin
from shared.paginations import StandardResultsSetPagination
from .serializers import SwitchDropdownSerializer
from shared.mixins import TrackCreatedUpdatedUserMixin



class SwitchListCreateView(TrackCreatedUpdatedUserMixin,generics.ListCreateAPIView):
    queryset = Switch.objects.all()
    serializer_class = SwitchSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']   


class SwitchRetrieveUpdateDestroyView(TrackCreatedUpdatedUserMixin,generics.RetrieveUpdateDestroyAPIView):
    queryset = Switch.objects.all()
    serializer_class = SwitchSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]


class SwitchDropdownListView(TrackCreatedUpdatedUserMixin,generics.ListAPIView):
    queryset = Switch.objects.all()
    serializer_class = SwitchDropdownSerializer
    permission_classes = [IsAuthenticated]  # You can modify permissions as needed
    pagination_class = None  # Disable pagination to return all items


from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Switch
from shared.mixins import TrackCreatedUpdatedUserMixin
from shared.permissions import IsSuperAdmin
import pandas as pd
from datetime import datetime

class BulkSwitchUpload(TrackCreatedUpdatedUserMixin, APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    HEADER_ALIASES = {
        "name": ["name", "switch name", "Switch", "Device Name"],
        "uid": ["uid", "unique id", "switch uid", "UID", "Unique ID"],
        "make": ["make", "brand", "manufacturer", "Make"],
        "model_number": ["model number", "model", "Model No", "model_number"],
        "serial_number": ["serial number", "serial", "Serial", "Serial No"],
        "package_date": ["package date", "packaged on", "Package Date", "Packaging Date"]
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
                data = {}

                # Map Excel columns to model fields
                for field, excel_col in header_map.items():
                    data[field] = row.get(excel_col)

                # Convert date field if needed
                if isinstance(data.get('package_date'), (int, float)):
                    try:
                        data['package_date'] = pd.to_datetime(data['package_date'], unit='d', origin='1899-12-30').date()
                    except:
                        data['package_date'] = None
                elif isinstance(data.get('package_date'), str):
                    try:
                        data['package_date'] = pd.to_datetime(data['package_date']).date()
                    except:
                        data['package_date'] = None

                uid = data.get('uid')
                if not uid:
                    errors.append(f"Row {index+1}: Missing UID")
                    continue

                try:
                    switch = Switch.objects.get(uid=uid)
                    for field, value in data.items():
                        setattr(switch, field, value)
                    switch.updated_by = request.user
                    switch.save()
                except Switch.DoesNotExist:
                    Switch.objects.create(**data, created_by=request.user, updated_by=request.user)

                success_count += 1

            return Response({
                "message": f"{success_count} switches uploaded/updated successfully",
                "errors": errors
            }, status=200)

        except Exception as e:
            return Response({'error': str(e)}, status=500)





from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated

from .models import OLT
from .serializers import OLTSerializer

class OLTListCreateView(
    TrackCreatedUpdatedUserMixin,
    generics.ListCreateAPIView
):
    serializer_class = OLTSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'uid']

    def get_queryset(self):
        user = self.request.user

        if user.is_super_admin:
            return OLT.objects.all().order_by('-id')

        elif hasattr(user, 'lco_profile'):
            return OLT.objects.filter(
                lco=user.lco_profile
            ).order_by('-id')

        return OLT.objects.none()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        response.data["is_super_admin"] = request.user.is_super_admin

        return response


class OLTRetrieveUpdateDestroyView(TrackCreatedUpdatedUserMixin,generics.RetrieveUpdateDestroyAPIView):
    queryset = OLT.objects.all()
    serializer_class = OLTSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]


from rest_framework import generics, permissions
from network.models import OLT
from network.serializers import OLTSerializer

class UnassignedOLTListView(TrackCreatedUpdatedUserMixin,generics.ListAPIView):
    queryset = OLT.objects.filter(lco__isnull=True)
    serializer_class = OLTSerializer
    permission_classes = [IsAuthenticated,IsSuperAdmin] 


from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import OLT
from network.models import Switch
from lcos.models import LCO
from shared.mixins import TrackCreatedUpdatedUserMixin
from shared.permissions import IsSuperAdmin
import pandas as pd

class BulkOLTUpload(TrackCreatedUpdatedUserMixin, APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    HEADER_ALIASES = {
        "name": ["olt name", "name", "OLT Name"],
        "uid": ["uid", "OLT UID"],
        "make": ["make", "brand"],
        "model_number": ["model", "model number"],
        "serial_number": ["serial", "serial number", "sn"],
        "package_date": ["package date", "pkg date", "date"],
        "lco_ref": ["lco code", "lco_ref"]
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
        file = request.FILES.get("file")
        switch_id = request.data.get("switch")

        if not file or not switch_id:
            return Response({"error": "Switch ID and file are required"}, status=400)

        try:
            switch = Switch.objects.get(pk=int(switch_id))
        except Switch.DoesNotExist:
            return Response({"error": "Invalid switch ID"}, status=404)

        try:
            df = pd.read_excel(file)
            header_map = self.normalize_headers(df)

            success_count = 0
            errors = []

            for index, row in df.iterrows():
                data = {}

                for field, excel_col in header_map.items():
                    data[field] = row.get(excel_col)

                if isinstance(data.get("package_date"), (int, float)):
                    try:
                        data["package_date"] = pd.to_datetime(data["package_date"], unit="d", origin="1899-12-30").date()
                    except:
                        data["package_date"] = None
                elif isinstance(data.get("package_date"), str):
                    try:
                        data["package_date"] = pd.to_datetime(data["package_date"]).date()
                    except:
                        data["package_date"] = None

                # Get LCO if present
                try:
                    data["lco"] = LCO.objects.get(lco_ref=data["lco_ref"]) if data.get("lco_ref") else None
                except:
                    data["lco"] = None

                if not data.get("uid"):
                    errors.append(f"Row {index+1}: Missing UID")
                    continue

                try:
                    olt, created = OLT.objects.update_or_create(
                        uid=data["uid"],
                        defaults={
                            "name": data.get("name"),
                            "make": data.get("make"),
                            "model_number": data.get("model_number"),
                            "serial_number": data.get("serial_number"),
                            "package_date": data.get("package_date"),
                            "switch": switch,
                            "lco": data.get("lco")
                        }
                    )
                    olt.updated_by = request.user
                    if created:
                        olt.created_by = request.user
                    olt.save()

                    success_count += 1
                except Exception as e:
                    errors.append(f"Row {index+1}: {str(e)}")

            return Response({
                "message": f"{success_count} OLTs uploaded/updated successfully",
                "errors": errors
            }, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)





from rest_framework.parsers import MultiPartParser, FormParser

class ISPCreateListView(generics.ListCreateAPIView):
    queryset = ISP.objects.all()
    serializer_class = ISPSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    parser_classes = (MultiPartParser, FormParser)



class ISPRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ISP.objects.all()
    serializer_class = ISPSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    parser_classes = (MultiPartParser, FormParser)



from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import ISP
from shared.mixins import TrackCreatedUpdatedUserMixin
from shared.permissions import IsSuperAdmin
import pandas as pd

class BulkISPUpload(TrackCreatedUpdatedUserMixin, APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    HEADER_ALIASES = {
        "name": ["isp name", "name", "ISP", "Name"],
        "address": ["address", "location", "Address", "ISP Address"]
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
                data = {}

                for field, excel_col in header_map.items():
                    data[field] = row.get(excel_col)

                if not data.get("name"):
                    errors.append(f"Row {index+1}: Missing ISP name")
                    continue

                try:
                    isp, created = ISP.objects.update_or_create(
                        name=data['name'],
                        defaults={"address": data.get("address", "")}
                    )

                    # Set audit fields
                    isp.updated_by = request.user
                    if created:
                        isp.created_by = request.user
                    isp.save()

                    success_count += 1
                except Exception as e:
                    errors.append(f"Row {index+1}: {str(e)}")

            return Response({
                "message": f"{success_count} ISPs uploaded/updated successfully",
                "errors": errors
            }, status=200)

        except Exception as e:
            return Response({'error': str(e)}, status=500)



from rest_framework.permissions import AllowAny
from .serializers import ISPPublicSerializer

class ISPPublicListView(generics.ListAPIView):
    queryset = ISP.objects.all().order_by('name')
    serializer_class = ISPPublicSerializer
    permission_classes = [AllowAny]


from rest_framework.views import APIView
from django.db.models import IntegerField, FloatField, Q
from django.db.models.functions import Cast
from customers.models import Customer
from customers.serializers import CustomerSerializer


class OltCustomerListView(APIView):
    pagination_class = StandardResultsSetPagination

    def get(self, request, olt_id):

        port = request.query_params.get("port")

        customers = Customer.objects.filter(
            olt_id=olt_id
        ).select_related('lco', 'isp', 'olt')

        customers = customers.filter(
            Q(port__regex=r'^\d+(\.\d+)?$') | Q(port__isnull=True) | Q(port="")
        )

        if port:
            customers = customers.annotate(
                port_float=Cast('port', FloatField()),
                port_int=Cast('port_float', IntegerField())
            ).filter(port_int=int(float(port)))

        
        unique_ports_qs = Customer.objects.filter(
            olt_id=olt_id
        ).filter(
            Q(port__regex=r'^\d+(\.\d+)?$')
        ).annotate(
            port_float=Cast('port', FloatField()),
            port_int=Cast('port_float', IntegerField())
        ).values_list('port_int', flat=True).distinct()

        #  Convert queryset to sorted list
        used_ports = sorted(list(unique_ports_qs))

        total_ports_used = len(used_ports)

        #  Pagination
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(customers, request)

        serializer = CustomerSerializer(paginated_queryset, many=True)

        return paginator.get_paginated_response({
            "total_customers": customers.count(),
            "total_ports_used": total_ports_used,
            "used_ports": used_ports,   
            "customers": serializer.data
        })