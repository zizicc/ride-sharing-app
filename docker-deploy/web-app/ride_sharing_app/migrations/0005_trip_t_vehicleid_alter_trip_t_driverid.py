# Generated by Django 5.1.5 on 2025-02-03 15:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ride_sharing_app', '0004_userprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='trip',
            name='t_vehicleid',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='trip',
            name='t_driverid',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
