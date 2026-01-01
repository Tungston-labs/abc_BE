
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
from rest_framework.parsers import MultiPartParser, FormParser
from .models import TicketAttachment

class LCOTicketCreateAPIView(generics.CreateAPIView):
    serializer_class = TicketSerializer
    permission_classes = [IsLCO]
    parser_classes = (MultiPartParser, FormParser)

    def perform_create(self, serializer):
        ticket = serializer.save(
            created_by=self.request.user,
            source='lco_app'
        )

        # handle multiple file uploads
        files = self.request.FILES.getlist("files")
        for file in files:
            TicketAttachment.objects.create(
                ticket=ticket,
                file=file
            )


from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django.utils.dateparse import parse_date

from .models import Ticket
from .serializers import TicketSerializer


class LCOTicketListAPIView(generics.ListAPIView):
    serializer_class = TicketSerializer
    permission_classes = [IsLCO]

    def get_queryset(self):
        user = self.request.user
        queryset = Ticket.objects.filter(created_by=user)

        # 🔹 Filter by date (YYYY-MM-DD)
        date = self.request.query_params.get("date")
        if date:
            parsed_date = parse_date(date)
            if parsed_date:
                queryset = queryset.filter(created_at__date=parsed_date)

        # 🔹 Filter by status
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status__iexact=status)

        # 🔹 Filter by priority
        priority = self.request.query_params.get("priority")
        if priority:
            queryset = queryset.filter(priority__iexact=priority)

        # 🔹 Filter by category
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category__iexact=category)

        # 🔹 Latest first
        return queryset.order_by("-created_at")



# ----------------------------ADMIN---------------------------




class TicketDetailUpdateDeleteAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsSuperAdmin]


from rest_framework import generics, permissions
from .models import Ticket
from .serializers import TicketSerializer

from rest_framework import generics
from django.db.models import Q
from django.utils.dateparse import parse_date

from .models import Ticket
from .serializers import TicketSerializer


class TicketListAPIView(generics.ListAPIView):
    serializer_class = TicketSerializer
    permission_classes = [IsSuperAdmin]

    def get_queryset(self):
        queryset = Ticket.objects.all()

        # 🔍 Search (name, phone, notes)
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(notes__icontains=search)
            )

        # 🟢 Filter by status
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status__iexact=status)

        # 🔥 Filter by priority
        priority = self.request.GET.get("priority")
        if priority:
            queryset = queryset.filter(priority__iexact=priority)

        # 🗂 Filter by category
        category = self.request.GET.get("category")
        if category:
            queryset = queryset.filter(category__iexact=category)

        # 📅 Filter by single date
        date = self.request.GET.get("date")
        if date:
            parsed_date = parse_date(date)
            if parsed_date:
                queryset = queryset.filter(created_at__date=parsed_date)

        # 📅 Filter by date range
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")

        if start_date and end_date:
            start = parse_date(start_date)
            end = parse_date(end_date)
            if start and end:
                queryset = queryset.filter(created_at__date__range=[start, end])

        # 📄 Latest first
        return queryset.order_by("-created_at")


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Ticket


class AdminTicketDashboardAPIView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        total_tickets = Ticket.objects.count()
        open_tickets = Ticket.objects.filter(status="open").count()
        in_progress_tickets = Ticket.objects.filter(status="in_progress").count()
        urgent_tickets = Ticket.objects.filter(priority="high").count()

        return Response({
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "in_progress_tickets": in_progress_tickets,
            "urgent_tickets": urgent_tickets
        })
