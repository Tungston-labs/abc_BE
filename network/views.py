from rest_framework import generics
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
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    pagination_class = StandardResultsSetPagination

class SwitchRetrieveUpdateDestroyView(TrackCreatedUpdatedUserMixin,generics.RetrieveUpdateDestroyAPIView):
    queryset = Switch.objects.all()
    serializer_class = SwitchSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]


class SwitchDropdownListView(TrackCreatedUpdatedUserMixin,generics.ListAPIView):
    queryset = Switch.objects.all()
    serializer_class = SwitchDropdownSerializer
    permission_classes = [IsAuthenticated]  # You can modify permissions as needed
    pagination_class = None  # Disable pagination to return all items


# network/views.py

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import OLT
from .serializers import OLTSerializer
from shared.permissions import IsSuperAdmin

class OLTListCreateView(TrackCreatedUpdatedUserMixin,generics.ListCreateAPIView):
    queryset = OLT.objects.all()
    serializer_class = OLTSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    pagination_class = StandardResultsSetPagination


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




class ISPCreateListView(generics.ListCreateAPIView):
    queryset = ISP.objects.all()
    serializer_class = ISPSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    pagination_class = StandardResultsSetPagination


class ISPRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ISP.objects.all()
    serializer_class = ISPSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]

