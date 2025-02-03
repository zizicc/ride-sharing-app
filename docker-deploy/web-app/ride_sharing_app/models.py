from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('passenger', 'Passenger'),
        ('driver', 'Driver'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)  
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='passenger')  
    was_driver = models.BooleanField(default=False) 

    def is_driver(self):
        return self.role == 'driver'
    
    def is_passenger(self):
        return self.role == 'passenger'
    
    def can_switch_to_driver(self):
        return self.was_driver

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

class Trip(models.Model):
    t_id = models.AutoField(primary_key=True)
    t_driverid = models.IntegerField(null=True, blank=True)
    t_vehicleid = models.IntegerField(null=True, blank=True)
    t_tripusersid = models.IntegerField()
    t_locationid = models.IntegerField()
    t_arrival_date_time = models.DateTimeField()
    t_shareno = models.IntegerField(default=0)
    t_isshareornot = models.BooleanField()
    t_status = models.CharField(max_length=50, default='open')
    
    def __str__(self):
        return f"Trip {self.t_id}"
    
