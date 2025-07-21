
from django.db import models
from shared.models import TimeStampedModel
from accounts.models import User
from network.models import OLT

class LCO(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lco_profile')
    name = models.CharField(max_length=255)
    address = models.TextField()
    aadhaar_number = models.CharField(max_length=12, unique=True)
    phone = models.CharField(max_length=15)

    def __str__(self):
        return self.name
