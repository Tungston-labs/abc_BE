import random
import string
from rest_framework import serializers
from django.db import models, IntegrityError
from rest_framework.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings

from network.models import OLT
from accounts.models import User
from .models import LCO
from network.serializers import OLTSerializer


class LCOSerializer(serializers.ModelSerializer):
    olts = serializers.PrimaryKeyRelatedField(
        queryset=OLT.objects.all(),
        many=True,
        write_only=True
    )

    email = serializers.EmailField(write_only=True)
    name = serializers.CharField()
    aadhaar_number = serializers.CharField()
    phone = serializers.CharField()
    address = serializers.CharField()

    olt_details = OLTSerializer(source='assigned_olts', many=True, read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    unique_id = serializers.CharField(read_only=True)

    class Meta:
        model = LCO
        fields = [
            'id', 'name', 'address', 'aadhaar_number', 'phone', 'email', 'olts',
            'olt_details', 'username', 'user_email', 'unique_id','networking_name','lco_code'
        ]

    def __init__(self, *args, **kwargs):
        """Dynamically adjust OLT queryset based on create or update."""
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.method in ['PUT', 'PATCH'] and self.instance:
            # Allow unassigned + currently assigned OLTs
            self.fields['olts'].queryset = OLT.objects.filter(
                models.Q(lco__isnull=True) | models.Q(lco_id=self.instance.id)
            )
        else:
            # Only unassigned OLTs for create
            self.fields['olts'].queryset = OLT.objects.filter(lco__isnull=True)

    def create(self, validated_data):
        email = validated_data.pop('email')
        name = validated_data.pop('name')
        aadhaar_number = validated_data.pop('aadhaar_number')
        phone = validated_data.pop('phone')
        address = validated_data.pop('address')
        olts = validated_data.pop('olts', [])
        networking_name = validated_data.pop('networking_name', None)
        lco_code = validated_data.pop('lco_code', None)

        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        try:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                phone=phone,
                is_lco=True
            )
        except IntegrityError:
            raise ValidationError({"email": "A user with this email already exists."})

        lco = LCO.objects.create(
            user=user,
            name=name,
            address=address,
            aadhaar_number=aadhaar_number,
            phone=phone,
            networking_name=networking_name,
            lco_code = lco_code
        )

        for olt in olts:
            olt.lco = lco
            olt.save()

        send_mail(
            subject="LCO Account Created",
            message=f"Username: {email}\nPassword: {password}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False
        )

        return lco

    def update(self, instance, validated_data):
        email = validated_data.pop('email', None)
        olts = validated_data.pop('olts', None)

        # Update LCO fields
        instance.name = validated_data.get('name', instance.name)
        instance.address = validated_data.get('address', instance.address)
        instance.aadhaar_number = validated_data.get('aadhaar_number', instance.aadhaar_number)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.networking_name = validated_data.get('networking_name', instance.networking_name)
        instance.lco_code = validated_data.get('lco_code', instance.lco_code)

        instance.save()

        # Update user email if provided
        if email:
            instance.user.email = email
            instance.user.username = email  # Keep username in sync
            instance.user.save()

        # Update OLT assignments if provided
        if olts is not None:
            OLT.objects.filter(lco=instance).update(lco=None)  # Unassign old ones
            for olt in olts:
                olt.lco = instance
                olt.save()

        return instance
