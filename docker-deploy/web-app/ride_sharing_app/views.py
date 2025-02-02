from django.shortcuts import render, redirect, reverse
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required

 
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