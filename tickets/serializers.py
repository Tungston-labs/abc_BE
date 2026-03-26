from rest_framework import serializers
from .models import Ticket,TicketAttachment


class TicketAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketAttachment
        fields = ["id", "file", "uploaded_at"]


class TicketSerializer(serializers.ModelSerializer):
    attachments = TicketAttachmentSerializer(many=True, read_only=True)
    lco_name = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = "__all__"

    def get_lco_name(self, obj):
        return obj.lco.name if obj.lco else None