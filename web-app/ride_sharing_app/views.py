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
from .gmail_service import send_email

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

    user_profile = request.user.userprofile

    if user_profile.role == 'driver':
        return redirect('driver_profile')
    elif user_profile.role == 'passenger':
        return redirect('passenger_profile')

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
        
        if DriverProfile.objects.filter(license_number=license_number).exists():
            return render(request, "register_driver.html", {"error": "This license number is already registered."})

        if Vehicle.objects.filter(license_plate=license_plate).exists():
            return render(request, "register_driver.html", {"error": "This license plate is already in use."})


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

    user_profile = request.user.userprofile

    if not user_profile.is_driver():
        return redirect('passenger_profile')

    driver = DriverProfile.objects.filter(user=request.user).first()

    vehicle = None
    if driver:
        vehicle = Vehicle.objects.filter(driver=driver).first()

    return render(request, 'driver/profile.html', {
        'driver': driver,
        'vehicle': vehicle
    })

@login_required
def passenger_profile(request):

    user_profile = request.user.userprofile

    if not user_profile.is_passenger():
        return redirect('driver_profile')

    return render(request, 'passenger/profile.html', {'user': request.user})

@login_required
def edit_vehicle(request):
    user_profile = request.user.userprofile  

    if not user_profile.is_driver():
        return redirect('passenger_profile')

    driver = DriverProfile.objects.filter(user=request.user).first()
    if not driver:
        return redirect('register_driver') 

    vehicle = Vehicle.objects.filter(driver=driver).first()

    if request.method == "POST":
        vehicle_type = request.POST.get("vehicle_type")
        license_plate = request.POST.get("license_plate")
        max_passengers = request.POST.get("max_passengers")
        additional_info = request.POST.get("additional_info")

        if vehicle:
            vehicle.vehicle_type = vehicle_type
            vehicle.license_plate = license_plate
            vehicle.max_passengers = max_passengers
            vehicle.additional_info = additional_info
            vehicle.save()
        else:
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
    user = request.user

    if request.method == 'POST':
        new_username = request.POST.get('username')
        new_email = request.POST.get('email')

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
    user = request.user

    if request.method == "POST":
        new_username = request.POST.get("username")
        new_email = request.POST.get("email")

        if not new_username or not new_email:
            messages.error(request, "Username and email cannot be empty.")
            return redirect("edit_driver_profile")

        user.username = new_username
        user.email = new_email
        user.save()
        messages.success(request, "Profile updated successfully.")

        return redirect("driver_profile")

    return render(request, "driver/edit_driver_profile.html", {"user": user})

@login_required
def edit_license(request):
    user = request.user

    driver_profile = DriverProfile.objects.filter(user=user).first()
    if not driver_profile:
        return redirect("driver_profile")

    if request.method == "POST":
        new_license = request.POST.get("license_number")

        if not new_license:
            messages.error(request, "License number cannot be empty.")
            return redirect("edit_license")

        driver_profile.license_number = new_license
        driver_profile.save()
        messages.success(request, "License number updated successfully.")

        return redirect("driver_profile")

    return render(request, "driver/edit_license.html", {"driver_profile": driver_profile})

@login_required
def start_trip(request):
    user_profile = request.user.userprofile

    if not user_profile.is_passenger():
        return redirect('driver_profile')

    if request.method == "POST":
        location_id = request.POST.get("location")
        arrival_date_time = request.POST.get("arrival_date_time")
        shareno = request.POST.get("shareno")
        is_shareornot = request.POST.get("is_shareornot") == "on"  

        try:
            location_id = int(location_id)
            if location_id < 1 or location_id > 20:
                raise ValueError
        except ValueError:
            messages.error(request, "Invalid location. Please select a number between 1 and 20.")
            return redirect("start_trip")

        if not arrival_date_time or not shareno:
            messages.error(request, "All fields are required.")
            return redirect("start_trip")

        new_trip = Trip.objects.create(
            t_locationid=location_id,
            t_arrival_date_time=arrival_date_time,
            t_shareno=shareno,
            t_isshareornot=is_shareornot
        )

        TripUsers.objects.create(trip=new_trip, user=request.user,passenger_number=shareno)

        messages.success(request, "Trip successfully created and you have joined the trip!")
        return redirect("passenger_profile")

    locations = range(1, 21) 
    return render(request, "passenger/start_trip.html", {"locations": locations})


@login_required
def search_trips(request):

    try:
       
        driver_profile = DriverProfile.objects.get(user=request.user)
        vehicle = Vehicle.objects.get(driver=driver_profile)
    except (DriverProfile.DoesNotExist, Vehicle.DoesNotExist):

        return render(request, "driver/search.html", {"open_trips": [], "locations": range(1, 21)})

    trips = Trip.objects.filter(t_status='open', t_shareno__lte=vehicle.max_passengers)
    
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
        
        passenger_ids = TripUsers.objects.filter(trip=trip).values_list('user_id', flat=True)

        passengers = User.objects.filter(id__in=passenger_ids)

        subject = "Trip Confirmation"
        body = f"""
        Dear Passenger,

        Your trip (Trip ID: {trip.t_id}) has been confirmed.
        Driver: {request.user.username}
        Vehicle: {vehicle.vehicle_type} ({vehicle.license_plate})

        Safe travels!
        """

        for passenger in passengers:
            send_email(passenger.email, subject, body)


        
        # send_trip_confirmation_email_with_gmail_api(trip)
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
    trips = Trip.objects.filter(t_status='open', t_isshareornot=True)

    # Filtering logic for search criteria...
    if request.method == "POST":
        arrival_address = request.POST.get("arrivalAddress", "").strip()
        start_time_str = request.POST.get("startTime", "").strip()
        end_time_str = request.POST.get("endTime", "").strip()
        customer_num = request.POST.get("customerNum", "").strip()
        vehicle_type = request.POST.get("v_type", "").strip()
        special_info = request.POST.get("v_specialInfo", "").strip()

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

    # Fetch trip-user relationships
    trip_users = TripUsers.objects.filter(trip__in=trips).values_list('trip_id', 'user_id')

    # Create a set of trips the current user is already part of
    current_user_id = request.user.id
    user_in_trip_map = {trip_id for trip_id, user_id in trip_users if user_id == current_user_id}

    locations = range(1, 21)
    context = {
        "open_trips": trips,
        "locations": locations,
        "user_in_trip_map": user_in_trip_map,  # Pass this directly to template
        "current_user_id": current_user_id,
    }
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

    trip_user_data = {tu.trip_id: tu.passenger_number for tu in TripUsers.objects.filter(user=request.user)}

    if request.method == "POST":
        trip_id = request.POST.get("trip_id")
        if not trip_id:
            return HttpResponse("Invalid request: trip_id is missing.", status=400)

        trip = get_object_or_404(Trip, t_id=trip_id)

        trip_user = TripUsers.objects.filter(trip=trip, user=request.user).first()
        if not trip_user:
            return HttpResponse("You are not authorized to edit this trip.", status=403)

        trip.t_locationid = request.POST.get("t_locationid")
        trip.t_arrival_date_time = request.POST.get("t_arrival_date_time")

        past_own_passenger_num = trip_user.passenger_number
        new_own_passenger_num = request.POST.get("update_own_passenger_num")

        if not new_own_passenger_num or not new_own_passenger_num.isdigit():
            return HttpResponse("Invalid input for passenger number.", status=400)

        new_own_passenger_num = int(new_own_passenger_num)
        num_change = new_own_passenger_num - past_own_passenger_num

        trip_user.passenger_number = new_own_passenger_num
        trip_user.save()

        trip.t_shareno = (trip.t_shareno or 0) + num_change
        trip.save()

        return redirect('myOpenTrip_passenger')

    for trip in trips:
        trip.own_passenger_num = trip_user_data.get(trip.t_id, 0)

    return render(request, "passenger/myOpenTrip.html", {"trips": trips})


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
            BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
            CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json") 
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES)
            # this is the redirect URI which should match your API setting, you can 
            # find this setting in Credentials/Authorized redirect URIs at the API setting portal
            # creds = flow.run_local_server(host='localhost', port=10000)
            creds = flow.run_local_server(port=10000)
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
    service = gmail_authenticate()


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
        send_message(service, "dwarfhamsterzhang@gmail.com", "recipient_email", subject, html_message)
