from django.db import models
from accounts.models import User
from shared.models import TimeStampedModel


class Ticket(TimeStampedModel):
    CATEGORY_CHOICES = (
        ("topup", "Top-up Request"),
        ("connection", "Connection Issue"),
        ("configuration", "Configuration Issue"),
        ("new_connection", "New Connection Request"),
        ("other", "Other"),
    )

    STATUS_CHOICES = (
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    )

    # Who created the ticket:
    created_by = models.ForeignKey(
        User,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        help_text="If created by LCO app"
    )

    source = models.CharField(
        max_length=20,
        choices=(("website", "Website"), ("lco_app", "LCO App")),
        default="website"
    )

    # Website user fields (public)
    name = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    notes = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="open"
    )

    admin_reply = models.TextField(
        blank=True, null=True,
        help_text="Admin response to the ticket"
    )

    def __str__(self):
        return f"{self.category} - {self.status}"

