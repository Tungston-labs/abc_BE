
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
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from tickets.models import Ticket
from tickets.serializers import TicketSerializer
from customers.management.commands.whatsapp import (
    send_ticket_update_whatsapp
)


class TicketDetailUpdateDeleteAPIView(generics.RetrieveUpdateDestroyAPIView):

    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):

        print("\n========== TICKET UPDATE ==========")

        old_ticket = self.get_object()
        old_status = old_ticket.status

        print("OLD STATUS:", old_status)

        ticket = serializer.save()

        print("NEW STATUS:", ticket.status)

        # Only send when status changes
        if old_status == ticket.status:

            print("STATUS NOT CHANGED")
            print("===================================\n")
            return

        print("STATUS CHANGED")

        # Send only for Resolved / Closed
        if str(ticket.status).lower() not in ["resolved", "closed"]:

            print("STATUS IS NOT RESOLVED/CLOSED")
            print("===================================\n")
            return

        try:

            if not ticket.lco:

                print("NO LCO ATTACHED")
                print("===================================\n")
                return

            print("LCO USER:", ticket.lco)

            # User -> LCO Profile
            if not hasattr(ticket.lco, "lco_profile"):

                print("NO LCO PROFILE FOUND")
                print("===================================\n")
                return

            lco_profile = ticket.lco.lco_profile

            print("LCO NAME:", lco_profile.name)
            print("LCO PHONE:", lco_profile.phone)

            if not lco_profile.phone:

                print("NO LCO PHONE FOUND")
                print("===================================\n")
                return

            phone = (
                lco_profile.phone
                .replace("+", "")
                .replace(" ", "")
                .replace("-", "")
            )

            if not phone.startswith("91"):
                phone = f"91{phone}"

            print("FINAL PHONE:", phone)

            result = send_ticket_update_whatsapp(
                phone=phone,
                lco_name=lco_profile.name,
                ticket_id=str(ticket.id),
                ticket_type=ticket.get_category_display(),
                status=ticket.get_status_display(),
                admin_reply=str(
                    getattr(ticket, "admin_reply", "")
                    or "No remarks provided"
                )
            )

            print("WHATSAPP RESULT:")
            print(result)

        except Exception as e:

            print("WHATSAPP ERROR:")
            print(str(e))

        print("===================================\n")

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

class TicketAttachmentDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            attachment = TicketAttachment.objects.get(id=pk)

            # OPTIONAL BUT IMPORTANT: safety check
            # (prevents deleting other tickets' attachments)
            if attachment.ticket.lco != request.user:
                return Response(
                    {"error": "Not allowed"},
                    status=status.HTTP_403_FORBIDDEN
                )

            attachment.delete()

            return Response(
                {"message": "deleted"},
                status=status.HTTP_200_OK
            )

        except TicketAttachment.DoesNotExist:
            return Response(
                {"error": "not found"},
                status=status.HTTP_404_NOT_FOUND
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

