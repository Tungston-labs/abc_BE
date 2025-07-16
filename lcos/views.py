from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import LCO
from .serializers import LCOSerializer
from shared.permissions import IsSuperAdmin
from rest_framework.pagination import PageNumberPagination

class LCOPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'

class LCOCreateListView(generics.ListCreateAPIView):
    queryset = LCO.objects.all()
    serializer_class = LCOSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    pagination_class = LCOPagination

class LCORetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = LCO.objects.all()
    serializer_class = LCOSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
