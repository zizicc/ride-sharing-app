from django.shortcuts import render, redirect, reverse
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import DriverProfile, Vehicle, Trip
 
# Views
@login_required
def home(request):
    return render(request, "home.html", {})
 
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        email = request.POST.get("email")

        if form.is_valid():
            user = form.save(commit=False)
            user.email = email
            user.set_password(form.cleaned_data.get('password1'))
            user.save()

            user = authenticate(username=user.username, password=form.cleaned_data.get('password1'))
            if user:
                login(request, user)
                return redirect('home')

        else:
            return render(request, 'registration/register.html', {'form': form})

    else:
        form = UserCreationForm()

    return render(request, 'registration/register.html', {'form': form})

@login_required
def register_driver(request):
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

        return redirect("home")  

    return render(request, "register_driver.html")

# search page for driver 
# @login_required
def driver_search(request):
    # rides = ride.objects.filter(r_state='OPEN').order_by('r_arrival_date_time')
    return render(request, 'driver/search.html', {})

# @login_required
def driver_ongoing(request):
    # rides = ride.objects.filter(r_state='OPEN').order_by('r_arrival_date_time')
    return render(request, 'driver/ongoing.html', {})

# @login_required
def driver_myDrive(request):
    # rides = ride.objects.filter(r_state='OPEN').order_by('r_arrival_date_time')
    return render(request, 'driver/myDrive.html', {})

# @login_required
def driver_profile(request):
    # rides = ride.objects.filter(r_state='OPEN').order_by('r_arrival_date_time')
    return render(request, 'driver/driverProfile.html', {})


def driver_search(request):
    # 获取所有状态为 'open' 的 trip 记录
    # open_trips = Trip.objects.filter(t_status='open')

    # 将查询结果传递到模板
    # return render(request, 'driver/search.html', {'open_trips': open_trips})
    all_trips = Trip.objects.all()  # 查询所有行程
    return render(request, 'driver/search.html', {'open_trips': all_trips})