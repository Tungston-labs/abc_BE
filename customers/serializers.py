# customers/serializers.py
from rest_framework import serializers
from .models import Customer
from lcos.models import LCO
from network.models import OLT, ISP

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'


class LCODropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = LCO
        fields = ['id', 'name']


class ISPDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = ISP
        fields = ['id', 'name']

