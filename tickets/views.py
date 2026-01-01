
from rest_framework import generics, permissions
from .models import Ticket
from .serializers import TicketSerializer
from shared.permissions import IsLCO,IsSuperAdmin
from shared.paginations import StandardResultsSetPagination


# -----------------------------------------------from website-public users

class WebsiteTicketCreateAPIView(generics.CreateAPIView):
    serializer_class = TicketSerializer
    permission_classes = []  # public

    def perform_create(self, serializer):
        serializer.save(source='website')

        # --------------------------------------from web app-by lco
class LCOTicketCreateAPIView(generics.CreateAPIView):
    serializer_class = TicketSerializer
    permission_classes = [IsLCO]

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            source='lco_app'
        )





# ----------------------------ADMIN---------------------------




class TicketDetailUpdateDeleteAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsSuperAdmin]


from rest_framework import generics, permissions
from .models import Ticket
from .serializers import TicketSerializer

class TicketListAPIView(generics.ListAPIView):
    serializer_class = TicketSerializer
    permission_classes = [IsSuperAdmin]

    def get_queryset(self):
        queryset = Ticket.objects.all()

        # Show only OPEN tickets by default
        status = self.request.GET.get("status", "Open")
        queryset = queryset.filter(status__iexact=status)

        # Filter by category (optional)
        category = self.request.GET.get("category")
        if category:
            queryset = queryset.filter(category__iexact=category)

        # Order latest first
        queryset = queryset.order_by("-created_at")

        return queryset
