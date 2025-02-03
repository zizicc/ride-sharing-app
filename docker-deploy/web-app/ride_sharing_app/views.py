from django.shortcuts import render, redirect, reverse
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Trip
 
# Views
@login_required
def home(request):
    return render(request, "registration/success.html", {})
 
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username = username, password = password)
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


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