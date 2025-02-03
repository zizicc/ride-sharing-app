# Generated by Django 5.1.5 on 2025-02-03 01:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ride_sharing_app', '0002_remove_driverprofile_additional_info_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Trip',
            fields=[
                ('t_id', models.AutoField(primary_key=True, serialize=False)),
                ('t_driverid', models.IntegerField()),
                ('t_tripusersid', models.IntegerField()),
                ('t_locationid', models.IntegerField()),
                ('t_arrival_date_time', models.DateTimeField()),
                ('t_shareno', models.IntegerField(default=0)),
                ('t_isshareornot', models.BooleanField()),
                ('t_status', models.CharField(default='open', max_length=50)),
            ],
        ),
    ]
