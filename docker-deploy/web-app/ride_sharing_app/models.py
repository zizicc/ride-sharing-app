from django.db import models
from django.contrib.auth.models import User

class DriverProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # combine with Django user
    license_number = models.CharField(max_length=20, unique=True)  
    is_approved = models.BooleanField(default=True) 

    def __str__(self):
        return f"{self.user.username} - {self.license_number}"
    
class Vehicle(models.Model):
    driver = models.OneToOneField(DriverProfile, on_delete=models.CASCADE)
    vehicle_type = models.CharField(max_length=50)
    license_plate = models.CharField(max_length=15, unique=True)
    max_passengers = models.IntegerField()
    additional_info = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.license_plate} ({self.vehicle_type})"