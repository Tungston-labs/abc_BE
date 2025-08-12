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
    lco_ref = serializers.SerializerMethodField(read_only=True)  # derived field
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

        read_only_fields = ['lco_ref']  # optionally make it read-only if it's derived

    def get_lco_ref(self, obj):
        return obj.lco.user.username if obj.lco and obj.lco.user else None



class LCODropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = LCO
        fields = ['id', 'name']


class ISPDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = ISP
        fields = ['id', 'name']

