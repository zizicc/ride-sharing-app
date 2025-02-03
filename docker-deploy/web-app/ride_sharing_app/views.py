from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserProfile, DriverProfile, Vehicle, Trip
from datetime import datetime
# Views
@login_required
def home(request):
    """ 根据用户角色跳转到对应的 Profile 页面 """
    user_profile = request.user.userprofile

    if user_profile.role == 'driver':
        return redirect('driver_profile')
    elif user_profile.role == 'passenger':
        return redirect('passenger_profile')

    # 防止异常情况，确保不会进入无限循环
    return redirect('passenger_profile')
 
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        email = request.POST.get("email")

        if form.is_valid():
            user = form.save(commit=False)
            user.email = email
            user.set_password(form.cleaned_data.get('password1'))
            user.save()

            user_profile = UserProfile.objects.create(user=user, role="passenger", was_driver=False)

            user = authenticate(username=user.username, password=form.cleaned_data.get('password1'))
            if user:
                login(request, user)
                return redirect('passenger_profile')

        else:
            return render(request, 'registration/register.html', {'form': form})

    else:
        form = UserCreationForm()

    return render(request, 'registration/register.html', {'form': form})

@login_required
def register_driver(request):
    user_profile = request.user.userprofile
    user = request.user

    if DriverProfile.objects.filter(user=user).exists():
        return render(request, "register_driver.html", {"error": "You are already a registered driver."})

    if request.method == "POST":
        license_number = request.POST.get("license_number")

        vehicle_type = request.POST.get("vehicle_type")
        license_plate = request.POST.get("license_plate")
        max_passengers = request.POST.get("max_passengers")
        additional_info = request.POST.get("additional_info")

        if not all([license_number, vehicle_type, license_plate, max_passengers]):
            return render(request, "register_driver.html", {"error": "All fields except additional info are required."})

        user_profile.role = 'driver'
        user_profile.is_driver = True
        user_profile.save()

        driver = DriverProfile.objects.create(
            user=user,
            license_number=license_number
        )

        Vehicle.objects.create(
            driver=driver,
            vehicle_type=vehicle_type,
            license_plate=license_plate,
            max_passengers=max_passengers,
            additional_info=additional_info
        )

        return redirect("driver_profile")  

    return render(request, "register_driver.html")

@login_required
def driver_profile(request):
    """ 司机个人信息页面 """
    user_profile = request.user.userprofile

    # 确保用户是司机
    if not user_profile.is_driver():
        return redirect('passenger_profile')

    # **正确查询 `DriverProfile`，使用 `request.user`**
    driver = DriverProfile.objects.filter(user=request.user).first()

    # **确保 `Vehicle` 查询的是 `DriverProfile`**
    vehicle = None
    if driver:
        vehicle = Vehicle.objects.filter(driver=driver).first()

    return render(request, 'driver/profile.html', {
        'driver': driver,
        'vehicle': vehicle
    })

@login_required
def passenger_profile(request):
    """ 乘客个人信息页面 """
    user_profile = request.user.userprofile

    # 确保只有乘客能访问
    if not user_profile.is_passenger():
        return redirect('driver_profile')

    return render(request, 'passenger/profile.html', {'user': request.user})

@login_required
def edit_vehicle(request):
    """ 允许司机修改车辆信息 """
    user_profile = request.user.userprofile

    # 确保只有司机能访问
    if not user_profile.is_driver():
        return redirect('passenger_profile')

    vehicle = Vehicle.objects.filter(driver=user_profile).first()
    if not vehicle:
        return redirect('driver_profile')

    if request.method == 'POST':
        vehicle.vehicle_type = request.POST.get('vehicle_type')
        vehicle.license_plate = request.POST.get('license_plate')
        vehicle.max_passengers = int(request.POST.get('max_passengers'))
        vehicle.special_info = request.POST.get('special_info', '')

        vehicle.save()
        return redirect('driver_profile')

    return render(request, 'driver/editVehicle.html', {'vehicle': vehicle})

@login_required
def edit_passenger(request):
    """ 允许乘客编辑个人信息 """
    user = request.user

    if request.method == 'POST':
        new_username = request.POST.get('username')
        new_email = request.POST.get('email')

        # 确保用户名和邮箱不为空
        if not new_username or not new_email:
            messages.error(request, "Username and email cannot be empty.")
            return redirect('edit_passenger')

        user.username = new_username
        user.email = new_email
        user.save()
        messages.success(request, "Profile updated successfully.")

        return redirect('passenger_profile')

    return render(request, 'passenger/editPassenger.html')

@login_required
def switch_role(request):
    user_profile = request.user.userprofile

    if user_profile.is_driver():
        user_profile.role = 'passenger'
        user_profile.was_driver = True
        user_profile.save()
        return redirect('passenger_profile')
    elif user_profile.was_driver and user_profile.is_passenger():
        user_profile.role = 'driver'
        user_profile.save()
        return redirect('driver_profile')
    else:
        return redirect('passenger_profile')
    

# search page for driver 
@login_required
def driver_search(request):
    # rides = ride.objects.filter(r_state='OPEN').order_by('r_arrival_date_time')
    return render(request, 'driver/search.html', {})

@login_required
def driver_ongoing(request):
    # rides = ride.objects.filter(r_state='OPEN').order_by('r_arrival_date_time')
    return render(request, 'driver/ongoing.html', {})

@login_required
def driver_myTrips(request):
    # rides = ride.objects.filter(r_state='OPEN').order_by('r_arrival_date_time')
    return render(request, 'driver/myTrips.html', {})


@login_required
def search_trips(request):

    trips = Trip.objects.filter(t_status='open')
    # trips = Trip.objects.all()
    
    if request.method == "POST":

        arrival_address = request.POST.get("arrivalAddress", "").strip()
        start_time_str   = request.POST.get("startTime", "").strip()
        end_time_str     = request.POST.get("endTime", "").strip()
        customer_num     = request.POST.get("customerNum", "").strip()
        vehicle_type     = request.POST.get("v_type", "").strip()
        special_info     = request.POST.get("v_specialInfo", "").strip()
        

        if arrival_address:
            trips = trips.filter(t_locationid=arrival_address)
        

        if start_time_str and end_time_str:
            try:
                start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
                end_time   = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
                trips = trips.filter(t_arrival_date_time__range=(start_time, end_time))
            except ValueError:

                pass
        elif start_time_str:
            try:
                start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
                trips = trips.filter(t_arrival_date_time__gte=start_time)
            except ValueError:
                pass
        elif end_time_str:
            try:
                end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
                trips = trips.filter(t_arrival_date_time__lte=end_time)
            except ValueError:
                pass
        

        if customer_num:
            try:
                num = int(customer_num)
                trips = trips.filter(t_shareno=num)
            except ValueError:
                pass
        

        
        if vehicle_type or special_info:
            vehicles = Vehicle.objects.all()
            if vehicle_type:
                vehicles = vehicles.filter(vehicle_type__icontains=vehicle_type)
            if special_info:
                vehicles = vehicles.filter(additional_info__icontains=special_info)
            vehicle_ids = vehicles.values_list("id", flat=True)
            trips = trips.filter(t_vehicleid__in=vehicle_ids)
    vehicle_ids = trips.values_list('t_vehicleid', flat=True)
    vehicles = Vehicle.objects.filter(id__in=vehicle_ids)
    vehicle_map = {v.id: v for v in vehicles}
    for trip in trips:
        trip.vehicle = vehicle_map.get(trip.t_vehicleid)

    context = {"open_trips": trips}
    return render(request, "driver/search.html", context)

@login_required
def join_trip(request, trip_id):

    if request.method == "POST":

        trip = get_object_or_404(Trip, pk=trip_id)
        
        try:
            driver_profile = DriverProfile.objects.get(user=request.user)
        except DriverProfile.DoesNotExist:
            return redirect('driverSearch')
        
        try:
            vehicle = Vehicle.objects.get(driver=driver_profile)
        except Vehicle.DoesNotExist:
            return redirect('driverSearch')
        
        trip.t_driverid = driver_profile.id  
        trip.t_vehicleid = vehicle.id
        trip.t_status = 'confirmed'
        trip.save()
        
        return redirect('driverSearch')
    else:
        return redirect('driverSearch')