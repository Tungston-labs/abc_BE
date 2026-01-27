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

    PRIORITY_CHOICES = (
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
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
    lco = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lco_tickets",
        help_text="LCO associated with this ticket"
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
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="medium"
    )

    def __str__(self):
        return f"{self.category} - {self.status}"


class TicketAttachment(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        related_name="attachments",
        on_delete=models.CASCADE
    )
    file = models.FileField(upload_to="tickets/attachments/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for Ticket {self.ticket.id}"