from django.urls import path
from .views import (
    WebsiteTicketCreateAPIView,
    LCOTicketCreateAPIView,
    TicketListAPIView,
    TicketDetailUpdateDeleteAPIView,LCOTicketListAPIView,AdminTicketDashboardAPIView
)

urlpatterns = [
    # Website (Public)
    path("public/", WebsiteTicketCreateAPIView.as_view(), name="website_ticket_create"),

    # LCO App (Authenticated)
    path("lco/", LCOTicketCreateAPIView.as_view(), name="lco_ticket_create"),
    path("list/lco/", LCOTicketListAPIView.as_view(), name="lco-ticket-list"),

    # Admin / Internal
    path("", TicketListAPIView.as_view(), name="ticket_list"),
    path("<int:pk>/", TicketDetailUpdateDeleteAPIView.as_view(), name="ticket_detail"),
    path(
        "admin/dashboard/",
        AdminTicketDashboardAPIView.as_view(),
        name="admin-ticket-dashboard"
    ),
]
