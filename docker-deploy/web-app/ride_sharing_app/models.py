# models.py 文件中的示例代码
from django.db import models

class Trip(models.Model):
    t_id = models.AutoField(primary_key=True)
    t_driverid = models.IntegerField()
    t_tripusersid = models.IntegerField()
    t_locationid = models.IntegerField()
    t_arrival_date_time = models.DateTimeField()
    t_shareno = models.IntegerField(default=0)
    t_isshareornot = models.BooleanField()
    t_status = models.CharField(max_length=50, default='open')
    
    def __str__(self):
        return f"Trip {self.t_id}"
