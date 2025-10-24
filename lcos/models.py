
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
    unique_id = models.CharField(max_length=50,unique=True,null=True,blank=True)
    networking_name = models.CharField(max_length=50,null=True, blank=True)
    lco_code = models.CharField(max_length=50,null=True, blank=True,unique=True)

    class Meta:
        ordering = ['id']


    def save(self, *args, **kwargs):
        if self.pk is None and not self.unique_id:  # new object only
            last_obj = LCO.objects.order_by('-id').first()
            if last_obj and last_obj.unique_id:
                try:
                    last_number = int(last_obj.unique_id.replace("LCO", ""))
                except ValueError:
                    last_number = 0
            else:
                last_number = 0
            self.unique_id = f"LCO{last_number + 1:03d}"
        super().save(*args, **kwargs)



    def __str__(self):
        return self.name
