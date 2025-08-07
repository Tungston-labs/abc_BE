
from django.db import models
from shared.models import TimeStampedModel
class Switch(TimeStampedModel):
    name = models.CharField(max_length=100)
    uid = models.CharField(max_length=100, unique=True)
    make = models.CharField(max_length=100)
    model_number = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100)
    package_date = models.DateField()
    unique_id = models.CharField(max_length=50,unique=True,null=True,blank=True)
    def save(self, *args, **kwargs):
        if not self.unique_id:
            last_switch = Switch.objects.order_by('-id').first()
            if last_switch and last_switch.unique_id:
                last_number = int(last_switch.unique_id.replace("SW", ""))
            else:
                last_number = 0
            self.unique_id = f"SW{last_number + 1:03d}"  # padded with zeros like SW001
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.uid})"
    


class OLT(TimeStampedModel):
    name = models.CharField(max_length=100)
    uid = models.CharField(max_length=100, unique=True)
    make = models.CharField(max_length=100)
    model_number = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100)
    package_date = models.DateField()
    switch = models.ForeignKey('network.Switch', on_delete=models.CASCADE, related_name='olts')
    lco = models.ForeignKey('lcos.LCO', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_olts')
    unique_id = models.CharField(max_length=50,unique=True,null=True,blank=True)



    def save(self, *args, **kwargs):
        if not self.unique_id:
            last_obj = OLT.objects.order_by('-id').first()
            if last_obj and last_obj.unique_id:
                last_number = int(last_obj.unique_id.replace("OLT", ""))
            else:
                last_number = 0
            self.unique_id = f"OLT{last_number + 1:03d}"
        super().save(*args, **kwargs)

    def __str__(self):

        return f"{self.name} ({self.uid})"



class ISP(TimeStampedModel):
    name = models.CharField(max_length=255)
    address = models.TextField()
    unique_id = models.CharField(max_length=50,unique=True,null=True,blank=True)


    def save(self, *args, **kwargs):
        if not self.unique_id:
            last_obj = ISP.objects.order_by('-id').first()
            if last_obj and last_obj.unique_id:
                last_number = int(last_obj.unique_id.replace("ISP", ""))
            else:
                last_number = 0
            self.unique_id = f"ISP{last_number + 1:03d}"
        super().save(*args, **kwargs)



    def __str__(self):
        return self.name

