from rest_framework import serializers
from .models import Ticket,TicketAttachment


class TicketAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketAttachment
        fields = ["id", "file", "uploaded_at"]


class TicketSerializer(serializers.ModelSerializer):
    lco_name = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = "__all__"

    def get_lco_name(self, obj):
        if obj.lco and hasattr(obj.lco, "lco_profile"):
            return obj.lco.lco_profile.name
        return None