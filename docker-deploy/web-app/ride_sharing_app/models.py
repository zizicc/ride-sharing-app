from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('passenger', 'Passenger'),
        ('driver', 'Driver'),
    ]
    id = models.AutoField(primary_key=True)
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

     # 反向访问 Vehicle，允许通过 driver_profile.vehicle 直接访问车辆信息
    @property
    def vehicle(self):
        return self.vehicle_set.first()  # 获取关联的 Vehicle（如果存在）

    def __str__(self):
        return f"{self.user.username} - {self.license_number}"
    
class Vehicle(models.Model):
    driver = models.OneToOneField(DriverProfile, on_delete=models.CASCADE, related_name="vehicle")
    vehicle_type = models.CharField(max_length=50)
    license_plate = models.CharField(max_length=15, unique=True)
    max_passengers = models.IntegerField()
    additional_info = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.license_plate} ({self.vehicle_type})"

class Trip(models.Model):
    t_id = models.AutoField(primary_key=True)
    t_driverid = models.IntegerField(null=True, blank=True)  # 司机ID（可空）
    t_vehicleid = models.IntegerField(null=True, blank=True)  # 车辆ID（可空）
    t_locationid = models.IntegerField()  # 目的地编号（必须是 1-20 的整数）
    t_arrival_date_time = models.DateTimeField()  # 到达时间
    t_shareno = models.IntegerField(default=0)  # 共享人数
    t_isshareornot = models.BooleanField()  # 是否共享
    t_status = models.CharField(max_length=50, default='open')  # 状态

    def __str__(self):
        return f"Trip {self.t_id} to location {self.t_locationid}"
    
class TripUsers(models.Model):
    tu_id = models.AutoField(primary_key=True)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)  # 关联 Trip
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # 关联 User（乘客）

    def __str__(self):
        return f"User {self.user.username} in Trip {self.trip.t_id}"
    
