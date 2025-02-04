from django.shortcuts import render, redirect, reverse
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserProfile, DriverProfile, Vehicle, Trip, TripUsers
 
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

            UserProfile.objects.create(user=user, role="passenger", was_driver=False)

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
        user_profile.was_driver = True
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
    user_profile = request.user.userprofile  # 获取 UserProfile

    # 确保用户是司机，否则跳转到乘客页面
    if not user_profile.is_driver():
        return redirect('passenger_profile')

    # 获取 DriverProfile
    driver = DriverProfile.objects.filter(user=request.user).first()
    if not driver:
        return redirect('register_driver')  # 司机信息缺失时跳转到注册司机页面

    # 获取车辆信息
    vehicle = Vehicle.objects.filter(driver=driver).first()

    if request.method == "POST":
        vehicle_type = request.POST.get("vehicle_type")
        license_plate = request.POST.get("license_plate")
        max_passengers = request.POST.get("max_passengers")
        additional_info = request.POST.get("additional_info")

        if vehicle:
            # 更新车辆信息
            vehicle.vehicle_type = vehicle_type
            vehicle.license_plate = license_plate
            vehicle.max_passengers = max_passengers
            vehicle.additional_info = additional_info
            vehicle.save()
        else:
            # 创建新车辆信息
            Vehicle.objects.create(
                driver=driver,
                vehicle_type=vehicle_type,
                license_plate=license_plate,
                max_passengers=max_passengers,
                additional_info=additional_info
            )

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
    
@login_required
def edit_driver_profile(request):
    """ 司机修改个人信息 """
    user = request.user

    if request.method == "POST":
        new_username = request.POST.get("username")
        new_email = request.POST.get("email")

        # 确保用户名和邮箱不能为空
        if not new_username or not new_email:
            messages.error(request, "Username and email cannot be empty.")
            return redirect("edit_driver_profile")

        # 更新用户信息
        user.username = new_username
        user.email = new_email
        user.save()
        messages.success(request, "Profile updated successfully.")

        return redirect("driver_profile")

    return render(request, "driver/edit_driver_profile.html", {"user": user})

@login_required
def edit_license(request):
    """ 司机修改 License Number """
    user = request.user

    # 确保当前用户有 DriverProfile
    driver_profile = DriverProfile.objects.filter(user=user).first()
    if not driver_profile:
        return redirect("driver_profile")

    if request.method == "POST":
        new_license = request.POST.get("license_number")

        # 确保 License Number 不能为空
        if not new_license:
            messages.error(request, "License number cannot be empty.")
            return redirect("edit_license")

        # 更新 License Number
        driver_profile.license_number = new_license
        driver_profile.save()
        messages.success(request, "License number updated successfully.")

        return redirect("driver_profile")

    return render(request, "driver/edit_license.html", {"driver_profile": driver_profile})
    
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Trip, TripUsers

@login_required
def start_trip(request):
    """ 乘客发起 Trip 并自动加入 TripUsers """
    user_profile = request.user.userprofile

    # 只有乘客可以发起 Trip
    if not user_profile.is_passenger():
        return redirect('driver_profile')

    if request.method == "POST":
        location_id = request.POST.get("location")
        arrival_date_time = request.POST.get("arrival_date_time")
        shareno = request.POST.get("shareno")
        is_shareornot = request.POST.get("is_shareornot") == "on"  # 复选框转换布尔值

        # 校验 location_id 是否在 1-20 范围内
        try:
            location_id = int(location_id)
            if location_id < 1 or location_id > 20:
                raise ValueError
        except ValueError:
            messages.error(request, "Invalid location. Please select a number between 1 and 20.")
            return redirect("start_trip")

        # 确保所有字段不为空
        if not arrival_date_time or not shareno:
            messages.error(request, "All fields are required.")
            return redirect("start_trip")

        # 创建 Trip
        new_trip = Trip.objects.create(
            t_locationid=location_id,
            t_arrival_date_time=arrival_date_time,
            t_shareno=shareno,
            t_isshareornot=is_shareornot
        )

        # 乘客自动加入 TripUsers
        TripUsers.objects.create(trip=new_trip, user=request.user)

        messages.success(request, "Trip successfully created and you have joined the trip!")
        return redirect("passenger_profile")

    locations = range(1, 21)  # 生成 1-20 的整数列表
    return render(request, "passenger/start_trip.html", {"locations": locations})


# search page for driver 
#@login_required
def driver_search(request):
    # rides = ride.objects.filter(r_state='OPEN').order_by('r_arrival_date_time')
    return render(request, 'driver/search.html', {})

# @login_required
def driver_ongoing(request):
    # rides = ride.objects.filter(r_state='OPEN').order_by('r_arrival_date_time')
    return render(request, 'driver/ongoing.html', {})

@login_required
def driver_myTrips(request):
    # rides = ride.objects.filter(r_state='OPEN').order_by('r_arrival_date_time')
    return render(request, 'driver/myTrips.html', {})


def driver_search(request):
    # 获取所有状态为 'open' 的 trip 记录
    # open_trips = Trip.objects.filter(t_status='open')

    # 将查询结果传递到模板
    # return render(request, 'driver/search.html', {'open_trips': open_trips})
    all_trips = Trip.objects.all()  # 查询所有行程
    return render(request, 'driver/search.html', {'open_trips': all_trips})