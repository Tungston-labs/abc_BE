from rest_framework import serializers
from .models import Ticket, TicketAttachment


class TicketAttachmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = TicketAttachment
        fields = ["id", "file", "uploaded_at"]


class TicketSerializer(serializers.ModelSerializer):

    lco_name = serializers.SerializerMethodField()
    customer_username = serializers.SerializerMethodField()
    customer_plan = serializers.SerializerMethodField()
    customer_olt = serializers.SerializerMethodField()
    customer_ont = serializers.SerializerMethodField()
    customer_port = serializers.SerializerMethodField()

    # For upload
    files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )

    # For response
    attachments = TicketAttachmentSerializer(
        many=True,
        read_only=True
    )

    class Meta:

        model = Ticket

        fields = "__all__"

    def get_lco_name(self, obj):

        if obj.lco and hasattr(obj.lco, "lco_profile"):

            return obj.lco.lco_profile.name

        return None
    
    def get_customer_username(self, obj):
        return obj.customer.username if obj.customer else None

    def get_customer_plan(self, obj):
        return obj.customer.plan if obj.customer else None

    def get_customer_olt(self, obj):
        return obj.customer.olt.name if obj.customer and obj.customer.olt else None

    def get_customer_ont(self, obj):
        return obj.customer.ont_number if obj.customer else None

    def get_customer_port(self, obj):
        return obj.customer.port if obj.customer else None

    def create(self, validated_data):

        validated_data.pop("files", None)

        ticket = Ticket.objects.create(**validated_data)

        return ticket
    
    def update(self, instance, validated_data):

        files = validated_data.pop("files", None)

        # update normal fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # handle file uploads
        if files:
            for file in files:
                TicketAttachment.objects.create(
                    ticket=instance,
                    file=file
                )

        return instance