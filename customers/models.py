# customers/models.py
from django.db import models
from lcos.models import LCO
from network.models import OLT, ISP
from django.utils import timezone
from shared.models import TimeStampedModel

class Customer(TimeStampedModel):
    profile_pic = models.ImageField(upload_to='customer_profiles/', null=True, blank=True)
    full_name = models.CharField(max_length=100,null=True, blank=True)
    phone = models.CharField(max_length=15,null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True,null=True, blank=True)

    lco = models.ForeignKey(LCO, on_delete=models.SET_NULL, null=True,blank=True)
    lco_ref = models.CharField(max_length=100, blank=True, null=True)
    mac_id = models.CharField(max_length=100,null=True, blank=True)
    plan = models.CharField(max_length=100,null=True, blank=True)
    v_lan = models.CharField(max_length=50,null=True, blank=True)
    isp = models.ForeignKey(ISP, on_delete=models.SET_NULL,null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    ont_number = models.CharField(max_length=100,null=True, blank=True)
    olt = models.ForeignKey(OLT, on_delete=models.SET_NULL, null=True, blank=True)
    signal = models.CharField(max_length=50,null=True, blank=True)
    kseb_post = models.CharField(max_length=100,null=True, blank=True)
    port = models.CharField(max_length=50,null=True, blank=True)
    distance = models.FloatField(help_text="Distance in meters",null=True,blank=True)
    username = models.CharField(max_length=50,null=True, blank=True)

    def __str__(self):
        return self.full_name

