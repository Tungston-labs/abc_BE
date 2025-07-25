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
