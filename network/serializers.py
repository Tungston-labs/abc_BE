# network/serializers.py

from rest_framework import serializers
from .models import Switch,OLT,ISP

class SwitchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Switch
        fields = '__all__'


class SwitchDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = Switch
        fields = ['id', 'name']


class OLTSerializer(serializers.ModelSerializer):

    switch_name = serializers.CharField(source='switch.name', read_only=True)

    class Meta:
        model = OLT
        fields = '__all__'



class ISPSerializer(serializers.ModelSerializer):
    logo = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = ISP
        fields = "__all__"
from rest_framework import serializers
from .models import ISP

class ISPPublicSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    class Meta:
        model = ISP
        fields = ["id", "name", "logo"]

    def get_logo(self, obj):
        request = self.context.get("request")
        if obj.logo and request:
            return request.build_absolute_uri(obj.logo.url)
        return None
