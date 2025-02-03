"""
URL configuration for ride_sharing_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('home/', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('register/driver/', views.register_driver, name = 'register_driver'),
    path('admin/', admin.site.urls),
    path('driver/search/', views.search_trips, name = 'driverSearch'),
    path('join/<int:trip_id>/', views.join_trip, name='join_trip'),
    path("mark_complete/<int:trip_id>/", views.mark_trip_complete, name="mark_trip_complete"),
    path('driver/ongoing/', views.ongoing_trips_for_driver, name = 'driverongoing'),
    path('driver/my_trip/', views.driver_myTrips, name = 'driver_myTrips'),
    path('driver/profile/', views.driver_profile, name = 'driver_profile'),
    path('driver/edit_vehicle/', views.edit_vehicle, name='edit_vehicle'),
    path('switch_role/', views.switch_role, name='switch_role'),
    path('passenger/profile/', views.passenger_profile, name = 'passenger_profile'),
    

    path('passenger/edit/', views.edit_passenger, name='edit_passenger'),

]

