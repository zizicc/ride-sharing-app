from django.db import models
from django.contrib.auth.models import User

class DriverProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # combine with Django user
    license_number = models.CharField(max_length=20, unique=True)  
    car_model = models.CharField(max_length=100)  
    vehicle_type = models.CharField(max_length=50)  
    license_plate = models.CharField(max_length=15, unique=True)  
    max_passengers = models.IntegerField()  
    phone_number = models.CharField(max_length=15)  
    additional_info = models.TextField(blank=True, null=True)  
    is_approved = models.BooleanField(default=True) 

    def __str__(self):
        return f"{self.user.username} - {self.license_plate} ({self.vehicle_type})"