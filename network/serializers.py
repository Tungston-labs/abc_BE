# network/serializers.py

from rest_framework import serializers
from .models import Switch,OLT,ISP

class SwitchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Switch
        fields = '__all__'




class OLTSerializer(serializers.ModelSerializer):

    switch_name = serializers.CharField(source='switch.name', read_only=True)

    class Meta:
        model = OLT
        fields = '__all__'




class ISPSerializer(serializers.ModelSerializer):
    class Meta:
        model = ISP
        fields = '__all__'

