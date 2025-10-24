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
    # Fully editable field
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
            'lco_name', 'isp_name', 'olt_name','username'
        ]



class LCODropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = LCO
        fields = ['id', 'name']


class ISPDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = ISP
        fields = ['id', 'name']

