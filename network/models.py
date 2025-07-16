
from django.db import models
from shared.models import TimeStampedModel

class Switch(TimeStampedModel):
    name = models.CharField(max_length=100)
    uid = models.CharField(max_length=100, unique=True)
    make = models.CharField(max_length=100)
    model_number = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100)
    package_date = models.DateField()

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

    def __str__(self):
        return f"{self.name} ({self.uid})"



class ISP(TimeStampedModel):
    name = models.CharField(max_length=255)
    address = models.TextField()

    def __str__(self):
        return self.name

