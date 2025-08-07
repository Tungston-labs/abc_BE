from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import ActivityLog
from .serializers import ActivityLogSerializer
from django.utils.dateparse import parse_date
from .paginations import StandardResultsSetPagination

class ActivityLogListView(ListAPIView):
    queryset = ActivityLog.objects.all().order_by('-timestamp')
    serializer_class = ActivityLogSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['user__username', 'user__email']
    ordering_fields = ['timestamp', 'action']
    pagination_class = StandardResultsSetPagination


    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by action
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action__icontains=action)

        # Filter by date range
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')

        if from_date:
            queryset = queryset.filter(timestamp__date__gte=parse_date(from_date))
        if to_date:
            queryset = queryset.filter(timestamp__date__lte=parse_date(to_date))

        return queryset
