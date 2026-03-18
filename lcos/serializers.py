
import random
import string
from rest_framework import serializers
from django.db import models, IntegrityError
from rest_framework.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from django.utils.text import slugify

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
    phone2 = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField()
    pincode = serializers.CharField()
    pincode2 = serializers.CharField(required=False, allow_blank=True)

    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)

    olt_details = OLTSerializer(source='assigned_olts', many=True, read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    unique_id = serializers.CharField(read_only=True)

    class Meta:
        model = LCO
        fields = [
            'id',
            'name',
            'address',
            'pincode',          # ✅
            'latitude',         # ✅
            'longitude',        # ✅
            'aadhaar_number',
            'phone',
            'email',
            'olts',
            'olt_details',
            'username',
            'user_email',
            'unique_id',
            'networking_name',
            'lco_code',
            'phone2',
            'pincode2', 
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.method in ['PUT', 'PATCH'] and self.instance:
            self.fields['olts'].queryset = OLT.objects.filter(
                models.Q(lco__isnull=True) | models.Q(lco_id=self.instance.id)
            )
        else:
            self.fields['olts'].queryset = OLT.objects.filter(lco__isnull=True)

    # ----------------------- CUSTOM USERNAME GENERATOR ------------------------
    def generate_username(self, name):
        base = f"ABC-{slugify(name)}"
        username = base
        counter = 1

        while User.objects.filter(username=username).exists():
            username = f"{base}-{counter}"
            counter += 1

        return username

    # --------------------------------------------------------------------------
    def create(self, validated_data):
        email = validated_data.pop('email')
        name = validated_data.pop('name')
        aadhaar_number = validated_data.pop('aadhaar_number')
        phone = validated_data.pop('phone')
        address = validated_data.pop('address')
        phone2 = validated_data.pop('phone2', None)
        pincode2 = validated_data.pop('pincode2', None) 

        # ✅ NEW
        pincode = validated_data.pop('pincode')
        latitude = validated_data.pop('latitude')
        longitude = validated_data.pop('longitude')

        olts = validated_data.pop('olts', [])
        networking_name = validated_data.pop('networking_name', None)
        lco_code = validated_data.pop('lco_code', None)

        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        username = self.generate_username(name)

        try:
            user = User.objects.create_user(
                username=username,
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
            pincode=pincode,        
            latitude=latitude,      
            longitude=longitude,    
            pincode2=pincode2,     
            phone2=phone2,         
            aadhaar_number=aadhaar_number,
            phone=phone,
            networking_name=networking_name,
            lco_code=lco_code
        )

        for olt in olts:
            olt.lco = lco
            olt.save()

        send_mail(
            subject="LCO Account Created",
            message=(
                f"Username: {username}\n"
                f"Email Login: {email}\n"
                f"Password: {password}"
            ),
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False
        )

        return lco

    def update(self, instance, validated_data):
        email = validated_data.pop('email', None)
        olts = validated_data.pop('olts', None)

        instance.name = validated_data.get('name', instance.name)
        instance.address = validated_data.get('address', instance.address)
        instance.pincode = validated_data.get('pincode', instance.pincode)      # ✅
        instance.latitude = validated_data.get('latitude', instance.latitude)  # ✅
        instance.longitude = validated_data.get('longitude', instance.longitude)# ✅
        instance.aadhaar_number = validated_data.get('aadhaar_number', instance.aadhaar_number)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.networking_name = validated_data.get('networking_name', instance.networking_name)
        instance.lco_code = validated_data.get('lco_code', instance.lco_code)
        instance.phone2 = validated_data.get('phone2', instance.phone2)
        instance.pincode2 = validated_data.get('pincode2', instance.pincode2)   
        instance.save()

        if email:
            instance.user.email = email
            instance.user.save()

        if olts is not None:
            OLT.objects.filter(lco=instance).update(lco=None)
            for olt in olts:
                olt.lco = instance
                olt.save()

        return instance



from rest_framework import serializers
from .models import LCO

class PublicLCOSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    class Meta:
        model = LCO
        fields = [
            'id',
            'name',
            'address',
            'phone',
            'pincode',
            'latitude',
            'longitude',
            'email',
            'networking_name',
            'phone2',
            
        ]
