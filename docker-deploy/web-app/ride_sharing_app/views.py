from django.shortcuts import render, redirect, reverse
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import DriverProfile
 
# Views
@login_required
def home(request):
    return render(request, "home.html", {})
 
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

@login_required
def register_driver(request):
    """允许已登录用户申请成为司机"""
    user = request.user

    if DriverProfile.objects.filter(user=user).exists():
        return render(request, "register_driver.html", {"error": "You are already a registered driver."})

    if request.method == "POST":
        license_number = request.POST.get("license_number")
        car_model = request.POST.get("car_model")
        vehicle_type = request.POST.get("vehicle_type")
        license_plate = request.POST.get("license_plate")
        max_passengers = request.POST.get("max_passengers")
        phone_number = request.POST.get("phone_number")
        additional_info = request.POST.get("additional_info")

        if not all([license_number, car_model, vehicle_type, license_plate, max_passengers, phone_number]):
            return render(request, "register_driver.html", {"error": "All fields except additional info are required."})

        DriverProfile.objects.create(
            user=user,
            license_number=license_number,
            car_model=car_model,
            vehicle_type=vehicle_type,
            license_plate=license_plate,
            max_passengers=max_passengers,
            phone_number=phone_number,
            additional_info=additional_info
        )

        return redirect("home")  # 申请成功后回到主页

    return render(request, "register_driver.html")