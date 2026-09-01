# customers/serializers.py
from rest_framework import serializers
from .models import Customer
from lcos.models import LCO
from network.models import OLT, ISP

from rest_framework import serializers
from .models import Customer
from lcos.models import LCO
from network.models import OLT,ISP

class CustomerSerializer(serializers.ModelSerializer):

    phone = serializers.CharField(
        required=False,
        allow_blank=True,
        validators=[]   
    )

    lco_ref = serializers.CharField(required=False, allow_blank=True)
    lco_name = serializers.CharField(source='lco.name', read_only=True)
    isp_name = serializers.CharField(source='isp.name', read_only=True)
    olt_name = serializers.CharField(source='olt.name', read_only=True)

    class Meta:
        model = Customer
        fields = [
            'id', 'profile_pic', 'full_name', 'phone', 'address', 'email',
            'last_updated', 'lco', 'lco_ref', 'mac_id', 'plan', 'v_lan',
            'isp', 'expiry_date', 'ont_number', 'olt', 'signal',
            'kseb_post', 'port', 'distance',
            'lco_name', 'isp_name', 'olt_name', 'username'
        ]


class LCODropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = LCO
        fields = ['id', 'name']


class ISPDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = ISP
        fields = ['id', 'name']

from rest_framework import serializers


class SignalItemSerializer(
    serializers.Serializer
):

    serial_number = serializers.CharField()

    mac_address = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True
    )

    rx_power = serializers.FloatField(
        required=False,
        allow_null=True
    )

    olt_ip = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True
    )

    port = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True
    )

    onu_id = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True
    )

    index = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True
    )

    updated_at = serializers.CharField(
        required=False,
        allow_null=True
    )


class SignalBatchSerializer(
    serializers.Serializer
):

    batch_id = serializers.CharField()

    batch_number = serializers.IntegerField()

    signals = SignalItemSerializer(
        many=True
    )