from rest_framework import serializers
from .models import Ticket,TicketAttachment


class TicketAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketAttachment
        fields = ["id", "file", "uploaded_at"]

class TicketSerializer(serializers.ModelSerializer):
    attachments = TicketAttachmentSerializer(many=True, read_only=True)
    lco_name = serializers.CharField(source="lco.name", read_only=True)


    class Meta:
        model = Ticket
        fields = "__all__"
        read_only_fields = ['created_by', 'source', 'created_at']

