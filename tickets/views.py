
from rest_framework import generics, permissions
from .models import Ticket
from .serializers import TicketSerializer
from shared.permissions import IsLCO,IsSuperAdmin
from shared.paginations import StandardResultsSetPagination


# -----------------------------------------------from website-public users

class WebsiteTicketCreateAPIView(generics.CreateAPIView):
    serializer_class = TicketSerializer
    permission_classes = []  # public
    pagination_class = StandardResultsSetPagination

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

        files = self.request.FILES.getlist("files")

        ticket = serializer.save(
            created_by=self.request.user,
            lco=self.request.user,
            source='lco_app'
        )

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


from django.db.models import Q
from django.utils.dateparse import parse_date

class LCOTicketListAPIView(generics.ListAPIView):
    serializer_class = TicketSerializer
    permission_classes = [IsLCO]
    pagination_class = StandardResultsSetPagination


    def get_queryset(self):
        user = self.request.user
        queryset = Ticket.objects.filter(lco=user)

        # 🔍 Search (ticket id / customer name)
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(id__icontains=search) |
                Q(name__icontains=search)
            )

        date = self.request.query_params.get("date")
        if date:
            parsed_date = parse_date(date)
            if parsed_date:
                queryset = queryset.filter(created_at__date=parsed_date)

        #  Status
        status = self.request.query_params.get("status")
        if status and status != "all":
            queryset = queryset.filter(status__iexact=status)

        #  Priority
        priority = self.request.query_params.get("priority")
        if priority and priority != "all":
            queryset = queryset.filter(priority__iexact=priority)

        #  Category
        category = self.request.query_params.get("category")
        if category and category != "all":
            queryset = queryset.filter(category__iexact=category)

        return queryset.order_by("-created_at")



# ----------------------------ADMIN---------------------------






from customers.management.commands.whatsapp import send_ticket_update_whatsapp

class TicketDetailUpdateDeleteAPIView(generics.RetrieveUpdateDestroyAPIView):

    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):

        old_ticket = self.get_object()
        old_status = old_ticket.status

        ticket = serializer.save()

        if (
            old_status != ticket.status
            and ticket.status in ["Resolved", "Closed"]
        ):

            if (
                ticket.lco
                and hasattr(ticket.lco, "lco_profile")
                and ticket.lco.phone
            ):

                phone = ticket.lco.phone.replace("+", "").replace(" ", "")

                if not phone.startswith("91"):
                    phone = f"91{phone}"

                send_ticket_update_whatsapp(
                    phone=phone,
                    lco_name=ticket.lco.lco_profile.name,
                    ticket_id=ticket.ticket_id,
                    ticket_type=ticket.ticket_type,
                    status=ticket.status,
                    admin_reply=ticket.admin_reply or "No remarks provided."
                )


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
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):

        queryset = Ticket.objects.select_related(
            "customer",
            "customer__olt",
            "lco",
            "created_by"
        )

        # Search
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(notes__icontains=search) |
                Q(customer__full_name__icontains=search) |
                Q(customer__username__icontains=search) |
                Q(customer__ont_number__icontains=search)
            )

        # Status
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status__iexact=status)

        # Priority
        priority = self.request.GET.get("priority")
        if priority:
            queryset = queryset.filter(priority__iexact=priority)

        # Category
        category = self.request.GET.get("category")
        if category:
            queryset = queryset.filter(category__iexact=category)

        # Single date
        date = self.request.GET.get("date")
        if date:
            parsed_date = parse_date(date)
            if parsed_date:
                queryset = queryset.filter(
                    created_at__date=parsed_date
                )

        # Date range
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")

        if start_date and end_date:
            start = parse_date(start_date)
            end = parse_date(end_date)

            if start and end:
                queryset = queryset.filter(
                    created_at__date__range=[start, end]
                )

        return queryset.order_by("-created_at", "-id")


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

