# customers/models.py
from django.db import models
from lcos.models import LCO
from network.models import OLT, ISP
from django.utils import timezone
from shared.models import TimeStampedModel

class Customer(TimeStampedModel):
    profile_pic = models.ImageField(upload_to='customer_profiles/', null=True, blank=True)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    email = models.EmailField()
    last_updated = models.DateTimeField(auto_now=True)

    lco = models.ForeignKey(LCO, on_delete=models.SET_NULL, null=True)
    lco_ref = models.CharField(max_length=100, blank=True, null=True)
    mac_id = models.CharField(max_length=100)
    plan = models.CharField(max_length=100)
    v_lan = models.CharField(max_length=50)
    isp = models.ForeignKey(ISP, on_delete=models.SET_NULL, null=True)
    expiry_date = models.DateField()
    ont_number = models.CharField(max_length=100)
    olt = models.ForeignKey(OLT, on_delete=models.SET_NULL, null=True)
    signal = models.CharField(max_length=50)
    kseb_post = models.CharField(max_length=100)
    port = models.CharField(max_length=50)
    distance = models.FloatField(help_text="Distance in meters",null=True,blank=True)

    def __str__(self):
        return self.full_name

