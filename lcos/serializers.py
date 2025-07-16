# network/serializers.py

import random
import string
from network.serializers import OLTSerializer
from rest_framework import serializers
from network.models import  OLT
from accounts.models import User
from django.core.mail import send_mail
from .models import LCO
from django.conf import settings

class LCOSerializer(serializers.ModelSerializer):
    olts = serializers.PrimaryKeyRelatedField(queryset=OLT.objects.all(), many=True, write_only=True)

    email = serializers.EmailField(write_only=True)  # Used only during creation
    name = serializers.CharField()
    aadhaar_number = serializers.CharField()
    phone = serializers.CharField()
    address = serializers.CharField()

    olt_details = OLTSerializer(source='olts', many=True, read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = LCO
        fields = [
            'id', 'name', 'address', 'aadhaar_number', 'phone', 'email', 'olts',
            'olt_details', 'username', 'user_email'
        ]

    def create(self, validated_data):
        email = validated_data.pop('email')
        name = validated_data.pop('name')
        aadhaar_number = validated_data.pop('aadhaar_number')
        phone = validated_data.pop('phone')
        address = validated_data.pop('address')
        olts = validated_data.pop('olts')

        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            phone=phone,
            is_lco=True
        )

        lco = LCO.objects.create(
            user=user,
            name=name,
            address=address,
            aadhaar_number=aadhaar_number,
            phone=phone
        )
        lco.olts.set(olts)

        send_mail(
            subject="LCO Account Created",
            message=f"Username: {email}\nPassword: {password}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False
        )

        return lco

