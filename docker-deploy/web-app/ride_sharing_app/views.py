from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserProfile, DriverProfile, Vehicle, Trip, TripUsers
from datetime import datetime
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.utils.dateparse import parse_datetime

import os.path
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

User = get_user_model() 
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
        TripUsers.objects.create(trip=new_trip, user=request.user,passenger_number=shareno)

        messages.success(request, "Trip successfully created and you have joined the trip!")
        return redirect("passenger_profile")

    locations = range(1, 21)  # 生成 1-20 的整数列表
    return render(request, "passenger/start_trip.html", {"locations": locations})


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
        
        
        def parse_datetime_local(dt_str):
            return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M") if dt_str else None

        start_time = parse_datetime_local(start_time_str)
        end_time = parse_datetime_local(end_time_str)

        if start_time and end_time:
            trips = trips.filter(t_arrival_date_time__range=(start_time, end_time))
        elif start_time:
            trips = trips.filter(t_arrival_date_time__gte=start_time)
        elif end_time:
            trips = trips.filter(t_arrival_date_time__lte=end_time)
        # if start_time_str and end_time_str:
        #     try:
        #         start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        #         end_time   = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
        #         trips = trips.filter(t_arrival_date_time__range=(start_time, end_time))
        #     except ValueError:
        #         pass
        # elif start_time_str:
        #     try:
        #         start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        #         trips = trips.filter(t_arrival_date_time__gte=start_time)
        #     except ValueError:
        #         pass
        # elif end_time_str:
        #     try:
        #         end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
        #         trips = trips.filter(t_arrival_date_time__lte=end_time)
        #     except ValueError:
        #         pass
        

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

    locations = range(1, 21)  # 生成 1-20 的整数列表

    context = {"open_trips": trips, "locations": locations}
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
        
        send_trip_confirmation_email_with_gmail_api(trip)
        trip.t_driverid = driver_profile.id  
        trip.t_vehicleid = vehicle.id
        trip.t_status = 'confirmed'
        trip.save()

        
        return redirect('driverSearch')
    else:
        return redirect('driverSearch')
    


@login_required
def ongoing_trips_for_driver(request):
    user_profile = UserProfile.objects.get(user=request.user)
    
    if user_profile.is_driver():  
        try:
            driver_profile = DriverProfile.objects.get(user=request.user)
            driver_id = driver_profile.id 
            
            trips = Trip.objects.filter(t_driverid=driver_id, t_status='confirmed')
        except DriverProfile.DoesNotExist:
            trips = []  
    else:
        trips = []

    return render(request, 'driver/ongoing.html', {'trips': trips})

@login_required
def complete_trips_for_driver(request):
    user_profile = UserProfile.objects.get(user=request.user)
    
    if user_profile.is_driver():  
        try:
            driver_profile = DriverProfile.objects.get(user=request.user)
            driver_id = driver_profile.id 
            
            trips = Trip.objects.filter(t_driverid=driver_id, t_status='complete')
        except DriverProfile.DoesNotExist:
            trips = []  
    else:
        trips = []

    return render(request, 'driver/myTrips.html', {'trips': trips})



def mark_trip_complete(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id)
    if trip.t_status == "confirmed":
        trip.t_status = "complete"
        trip.save()
    return redirect('driverongoing') 

@login_required
def search_passenger(request):

    # trips = Trip.objects.filter(t_status='open')
    trips = Trip.objects.filter(t_status='open', t_isshareornot=True)
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
        

        def parse_datetime_local(dt_str):
            return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M") if dt_str else None

        start_time = parse_datetime_local(start_time_str)
        end_time = parse_datetime_local(end_time_str)

        if start_time and end_time:
            trips = trips.filter(t_arrival_date_time__range=(start_time, end_time))
        elif start_time:
            trips = trips.filter(t_arrival_date_time__gte=start_time)
        elif end_time:
            trips = trips.filter(t_arrival_date_time__lte=end_time)

        # if start_time_str and end_time_str:
        #     try:
        #         start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        #         end_time   = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
        #         trips = trips.filter(t_arrival_date_time__range=(start_time, end_time))
        #     except ValueError:

        #         pass
        # elif start_time_str:
        #     try:
        #         start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        #         trips = trips.filter(t_arrival_date_time__gte=start_time)
        #     except ValueError:
        #         pass
        # elif end_time_str:
        #     try:
        #         end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
        #         trips = trips.filter(t_arrival_date_time__lte=end_time)
        #     except ValueError:
        #         pass
        

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

    locations = range(1, 21) 

    context = {"open_trips": trips, "locations": locations}
    # context = {"open_trips": trips}
    return render(request, "passenger/search.html", context)

@login_required
def join_trip_as_sharer(request, trip_id):
    trip = get_object_or_404(Trip, t_id=trip_id)

    if request.method == "POST":
        try:
            num_passengers = int(request.POST.get("num_passengers", 1)) 
            if num_passengers < 1:
                return HttpResponse("Invalid passenger number.", status=400)

            trip.t_shareno += num_passengers
            trip.save()

            if not TripUsers.objects.filter(trip=trip, user=request.user,passenger_number=num_passengers).exists():
                TripUsers.objects.create(trip=trip, user=request.user,passenger_number=num_passengers)
            
            return redirect('search_passenger') 

            
        except ValueError:
            return HttpResponse("Invalid input.", status=400)

    return render(request, "search_passenger.html", {"trip": trip})

from django.shortcuts import redirect
@login_required
def myOpenTrip_passenger(request):
    trip_ids = TripUsers.objects.filter(user=request.user).values_list('trip_id', flat=True)
    trips = Trip.objects.filter(t_id__in=trip_ids, t_status="open").order_by("t_arrival_date_time")

    # 预计算所有 trip 的 ownPassengerNum
    trip_user_data = {tu.trip_id: tu.passenger_number for tu in TripUsers.objects.filter(user=request.user)}

    if request.method == "POST":
        trip_id = request.POST.get("trip_id")
        if not trip_id:
            return HttpResponse("Invalid request: trip_id is missing.", status=400)

        trip = get_object_or_404(Trip, t_id=trip_id)

        # 确保当前用户有权限修改这个 trip
        trip_user = TripUsers.objects.filter(trip=trip, user=request.user).first()
        if not trip_user:
            return HttpResponse("You are not authorized to edit this trip.", status=403)

        # 更新 trip 相关信息
        trip.t_locationid = request.POST.get("t_locationid")
        trip.t_arrival_date_time = request.POST.get("t_arrival_date_time")

        # 计算新的 own_passenger_num
        past_own_passenger_num = trip_user.passenger_number
        new_own_passenger_num = request.POST.get("update_own_passenger_num")

        if not new_own_passenger_num or not new_own_passenger_num.isdigit():
            return HttpResponse("Invalid input for passenger number.", status=400)

        new_own_passenger_num = int(new_own_passenger_num)
        num_change = new_own_passenger_num - past_own_passenger_num

        # ✅ 更新 `TripUsers` 表中的 passenger_number
        trip_user.passenger_number = new_own_passenger_num
        trip_user.save()

        # ✅ 更新 `Trip` 表中的 `t_shareno`
        trip.t_shareno = (trip.t_shareno or 0) + num_change
        trip.save()

        # 🔄 避免重复提交问题，重定向到 GET
        return redirect('myOpenTrip_passenger')

    # 在 trip 对象中存储 own_passenger_num，方便模板访问
    for trip in trips:
        trip.own_passenger_num = trip_user_data.get(trip.t_id, 0)

    return render(request, "passenger/myOpenTrip.html", {"trips": trips})



# @login_required
# def myOpenTrip_passenger(request):

#     # trip_ids = TripUsers.objects.filter(user=request.user).values_list('trip_id', flat=True)
#     # trips = Trip.objects.filter(t_id__in=trip_ids, t_status="open")
#     trip_ids = TripUsers.objects.filter(user=request.user).values_list('trip_id', flat=True)
#     trips = Trip.objects.filter(t_id__in=trip_ids, t_status="open").order_by("t_arrival_date_time")

#     if request.method == "POST":
#         trip_id = request.POST.get("trip_id")
#         if not trip_id:
#             return HttpResponse("Invalid request: trip_id is missing.", status=400)
#         trip = get_object_or_404(Trip, t_id=trip_id)

#         if not TripUsers.objects.filter(trip=trip, user=request.user).exists():
#             return HttpResponse("You are not authorized to edit this trip.", status=403)

#         trip.t_locationid = request.POST.get("t_locationid")
#         trip.t_arrival_date_time = request.POST.get("t_arrival_date_time")
#         # trip.t_shareno = request.POST.get("t_shareno")
#         # get past passenger number
#         trip_user = TripUsers.objects.filter(trip=trip, user=request.user).first()
#         past_passenger_num = trip_user.passenger_number if trip_user else 0  
#         num_change = int(request.POST.get("t_shareno")) - past_passenger_num
#         trip.t_shareno = (trip.t_shareno or 0) + num_change
#         print("DEBUG: POST DATA ->", request.POST) 

#         trip.save()
#         # return redirect('myOpenTrip_passenger') 

#     return render(request, "passenger/myOpenTrip.html", {"trips": trips, "ownPassengerNum": past_passenger_num})

@login_required
def myConfirmedTrip_passenger(request):
    
    trip_ids = TripUsers.objects.filter(user=request.user).values_list('trip_id', flat=True)
    trips = Trip.objects.filter(t_id__in=trip_ids, t_status="confirmed").order_by("t_arrival_date_time")
    trip_data = []
    for trip in trips:
        driver_profile = None
        vehicle = None

        if trip.t_driverid:

            driver_profile = DriverProfile.objects.filter(id=trip.t_driverid).first()
            if driver_profile: 
                driver_user_info = User.objects.filter(id=driver_profile.user_id).first() 
                vehicle = Vehicle.objects.filter(driver_id=driver_profile.id).first()
 
        trip_data.append({
            "trip": trip,
            "driver": driver_profile,
            "vehicle": vehicle,
            "driver_user_info":driver_user_info
        })

    return render(request, "passenger/myConfirmedTrip.html", {"trip_data": trip_data})

@login_required
def myCompleteTrip_passenger(request):
    
    trip_ids = TripUsers.objects.filter(user=request.user).values_list('trip_id', flat=True)
    trips = Trip.objects.filter(t_id__in=trip_ids, t_status="complete").order_by("-t_arrival_date_time")
    trip_data = []
    for trip in trips:
        driver_profile = None
        vehicle = None

        if trip.t_driverid:

            driver_profile = DriverProfile.objects.filter(id=trip.t_driverid).first()
            if driver_profile: 
                driver_user_info = User.objects.filter(id=driver_profile.user_id).first() 
                vehicle = Vehicle.objects.filter(driver_id=driver_profile.id).first()
 
        trip_data.append({
            "trip": trip,
            "driver": driver_profile,
            "vehicle": vehicle,
            "driver_user_info":driver_user_info
        })

    return render(request, "passenger/myCompleteTrip.html", {"trip_data": trip_data})


# Authentication and service creation
def gmail_authenticate():
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    creds = None
    # token.json stored user access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # Authentication if no valid credentials are available
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # This credentials.json is the credential you download from Google API portal when you 
            # created the OAuth 2.0 Client IDs
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 获取当前文件所在目录
            CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")  # 绝对路径
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES)
            # this is the redirect URI which should match your API setting, you can 
            # find this setting in Credentials/Authorized redirect URIs at the API setting portal
            creds = flow.run_local_server(host='vcm-45974.vm.duke.edu', port=5000)
        # Save vouchers for later use
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

# Create and send emails
def send_message(service, sender, to, subject, msg_html):
    message = MIMEMultipart('alternative')
    message['from'] = sender
    message['to'] = to
    message['subject'] = subject

    msg = MIMEText(msg_html, 'html')
    message.attach(msg)

    raw = base64.urlsafe_b64encode(message.as_bytes())
    raw = raw.decode()
    body = {'raw': raw}

    message = (service.users().messages().send(userId="me", body=body).execute())
    print(f"Message Id: {message['id']}")


def send_trip_confirmation_email_with_gmail_api(trip):
    """ 通过 Gmail API 发送 Trip 确认邮件给所有乘客 """
    service = gmail_authenticate()


    # 获取该 trip 所有乘客的邮箱
    trip_users = TripUsers.objects.filter(trip=trip)
    recipient_emails = [user.user.email for user in trip_users if user.user.email]

    if not recipient_emails:
        print("no user")
        return

    subject = "Your trip has been confirmed"
    html_message = f"""
    <html>
    <body>
        <p>Hi, your trip  <strong>{trip.t_id}</strong> has been confirmed</p >
        <p><strong>Destination:</strong> {trip.t_locationid}</p >
        <p><strong>Arrival time:</strong> {trip.t_arrival_date_time}</p >
    </body>
    </html>
    """

    for recipient_email in recipient_emails:
        send_message(service, "yazi.wang22@gmail.com", "recipient_email", subject, html_message)
