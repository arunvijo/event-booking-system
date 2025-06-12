from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,permissions
from .models import *
from .serializers import *
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.core.mail import EmailMessage
from django.shortcuts import render,redirect
from django.contrib import messages
import os
import base64
from PIL import Image
import numpy as np
import cv2
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import os
from io import BytesIO
from email.mime.image import MIMEImage
from email.utils import make_msgid
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum,Count
from django.http import JsonResponse
import json

# Create your views here.
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Event
from .serializers import EventSerializer
from django.contrib.auth.models import AnonymousUser

import json
from django.db.models import Sum, Count
from django.shortcuts import render
from .models import Event, Booking
from django.db.models.functions import TruncDate, TruncHour



from django.shortcuts import render
from django.db.models import Sum, Count
from django.utils.timezone import localtime
from collections import defaultdict
import json
from django.http import HttpResponse


def admin_dashboard(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('admin_login')

    events = Event.objects.all()
    total_events = events.count()
    total_bookings = Booking.objects.count()
    total_seats_booked = Booking.objects.aggregate(total=Sum('seats_booked'))['total'] or 0
    total_available_seats = events.aggregate(total=Sum('available_seats'))['total'] or 0

    # Booking over time (grouped by date)
    booking_qs = Booking.objects.all()
    booking_dict = defaultdict(int)
    for b in booking_qs:
        date_key = localtime(b.booking_time).strftime('%Y-%m-%d')
        booking_dict[date_key] += 1
    bookings_over_time = [{'date': k, 'count': v} for k, v in sorted(booking_dict.items())]

    # Peak hours (grouped by hour of day)
    peak_dict = defaultdict(int)
    for b in booking_qs:
        hour = localtime(b.booking_time).hour
        peak_dict[hour] += 1
    peak_hours = [{'hour': k, 'count': v} for k, v in sorted(peak_dict.items())]

    return render(request, 'admin/dashboard.html', {
        'events': events,
        'total_events': total_events,
        'total_bookings': total_bookings,
        'total_seats_booked': total_seats_booked,
        'total_available_seats': total_available_seats,
        'bookings_over_time': json.dumps(bookings_over_time),
        'peak_hours': json.dumps(peak_hours),
    })



@csrf_exempt
def admin_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            return render(request, 'admin/login.html', {'error': 'Invalid credentials or not a superuser'})
    return render(request, 'admin/login.html')




@user_passes_test(lambda u: u.is_superuser)
def admin_add_event(request):
    if request.method == 'POST':
        serializer = EventSerializer(data=request.POST)
        if serializer.is_valid():
            serializer.save()
            return redirect('admin_dashboard')
        else:
            return render(request, 'admin/add_event.html', {'errors': serializer.errors})
    return render(request, 'admin/add_event.html')


@user_passes_test(lambda u: u.is_superuser)
def admin_edit_event(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        serializer = EventSerializer(event, data=request.POST, partial=True)
        if serializer.is_valid():
            serializer.save()
            return redirect('admin_dashboard')
        else:
            return render(request, 'admin/edit_event.html', {'errors': serializer.errors, 'event': serializer.data})
    else:
        serializer = EventSerializer(event)
        return render(request, 'admin/edit_event.html', {'event': serializer.data})


def send_booking_email(to_email, event, seats, qr_path):
    subject = f'Your Booking for {event.name} is Confirmed!'
    total_price = event.price * seats
    event_datetime = event.date.strftime('%A, %d %B %Y | %I:%M %p')

    # Generate CIDs
    qr_cid = make_msgid(domain='eventmail.local')[1:-1]
    event_cid = make_msgid(domain='eventmail.local')[1:-1]

    # Plain Text Body
    text_body = (
        f"Your booking for {event.name} is confirmed!\n\n"
        f"Date & Time: {event_datetime}\n"
        f"Location: {event.location}\n"
        f"Organizer: {event.organizer}\n"
        f"Seats Booked: {seats}\n"
        f"Total Price: ₹{total_price:.2f}\n\n"
        f"QR code and event image are attached.\n"
    )

    # HTML Body using CID for images
    html_body = f"""
    <html>
    <body style="margin:0; padding:0; background-color:#121212; font-family:Arial,sans-serif; color:#f0f0f0;">
    <div style="max-width:600px; margin:20px auto; background:linear-gradient(145deg,#1e1e1e,#2a2a2a); border:1px solid #3a3a3a; border-radius:20px; box-shadow:0 8px 20px rgba(0,0,0,0.5); padding:20px;">

        <h2 style="text-align:center; color:#27ae60;">🎟️ Booking Confirmed</h2>
        <p style="text-align:center; color:#ccc;">Your booking for <strong>{event.name}</strong> is confirmed!</p>

        {'<div style="text-align:center;"><img src="cid:{}" style="width:100%; max-width:300px; border-radius:12px; object-fit:cover;" alt="Event Image" /></div>'.format(event_cid) if event.image else ''}

        <table style="width:100%; font-size:14px; margin-top:20px;">
            <tr><td><strong>Date & Time:</strong></td><td>{event_datetime}</td></tr>
            <tr><td><strong>Location:</strong></td><td>{event.location or 'To be announced'}</td></tr>
            <tr><td><strong>Organizer:</strong></td><td>{event.organizer or 'Event Team'}</td></tr>
            <tr><td><strong>Seats Booked:</strong></td><td>{seats}</td></tr>
            <tr><td><strong>Total Price:</strong></td><td>₹{total_price:.2f}</td></tr>
        </table>

        <div style="margin-top:20px;">
            <p><strong>Event Description:</strong></p>
            <p style="background-color:#1b1b1b; padding:10px 15px; border-left:4px solid #27ae60; color:#bbbbbb;">
                {event.description or 'No additional description provided.'}
            </p>
        </div>

        <div style="text-align:center; margin-top:20px;">
            <p>📎 Present this QR code at the event venue:</p>
            <img src="cid:{qr_cid}" style="width:120px; height:120px; border-radius:10px; border:1px solid #444;" alt="QR Code" />
        </div>

        <p style="text-align:center; font-size:13px; color:#888; margin-top:30px;">
            This is an automated email. Please do not reply.<br>
            Regards, <strong>{event.organizer or 'Event Team'}</strong>
        </p>

    </div>
    </body>
    </html>
    """

    try:
        email = EmailMultiAlternatives(subject, text_body, settings.EMAIL_HOST_USER, [to_email])
        email.attach_alternative(html_body, "text/html")

        # Attach inline QR image
        if os.path.exists(qr_path):
            with open(qr_path, 'rb') as f:
                qr_image = MIMEImage(f.read())
                qr_image.add_header('Content-ID', f'<{qr_cid}>')
                qr_image.add_header('Content-Disposition', 'inline', filename='qr.png')
                email.attach(qr_image)

        # Attach inline Event image
        if event.image and hasattr(event.image, 'path') and os.path.exists(event.image.path):
            with open(event.image.path, 'rb') as f:
                event_image = MIMEImage(f.read())
                event_image.add_header('Content-ID', f'<{event_cid}>')
                event_image.add_header('Content-Disposition', 'inline', filename='event.jpg')
                email.attach(event_image)

        # Optional: Attach as files too
        # if os.path.exists(qr_path):
        #     email.attach_file(qr_path)
        # if event.image and hasattr(event.image, 'path') and os.path.exists(event.image.path):
        #     email.attach_file(event.image.path)

        email.send()
        print("Email sent successfully with visible inline images!")
    except Exception as e:
        print("Error sending email:", e)



def logout_view(request):
    request.session.flush()
    messages.success(request, "You have been logged out successfully.")
    return redirect('login') 


class EventDetailAPIView(APIView):
    def get_object(self, pk):
        return get_object_or_404(Event, pk=pk)

    def put(self, request, pk, format=None):
        event = self.get_object(pk)
        serializer = EventSerializer(event, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EventAPIView(APIView):
    def get(self, request, pk=None):
        if pk:
            # Detail view logic
            event = get_object_or_404(Event, pk=pk)
            serializer = EventSerializer(event)
            return render(request, 'events.html', {
                'event': serializer.data,
                'user': request.session.get('username'),
                'tokens': {
                    'refresh': request.session.get('refresh'),
                    'access': request.session.get('access')
                }
            })

        # List view logic
        events = Event.objects.all()
        search_query = request.GET.get('search')
        if search_query:
            events = events.filter(name__icontains=search_query)

        location_filter = request.GET.get('location')
        if location_filter:
            events = events.filter(location__iexact=location_filter)

        sort_by = request.GET.get('sort')
        if sort_by == 'date':
            events = events.order_by('date')

        serializer = EventSerializer(events, many=True)
        unique_locations = Event.objects.values_list('location', flat=True).distinct()

        return render(request, 'events.html', {
            'events': serializer.data,
            'unique_locations': unique_locations,
            'user': request.session.get('username'),
            'tokens': {
                'refresh': request.session.get('refresh'),
                'access': request.session.get('access')
            }
        })

    def post(self, request):
        if not request.user or not request.user.is_authenticated or not request.user.is_superuser:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        serializer = EventSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Event created successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        if not request.user or not request.user.is_authenticated or not request.user.is_superuser:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        event = get_object_or_404(Event, pk=pk)
        serializer = EventSerializer(event, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Event updated successfully"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if not request.user or not request.user.is_authenticated or not request.user.is_superuser:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        event = get_object_or_404(Event, pk=pk)
        event.delete()
        return Response({"message": "Event deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class RegisterAPIView(APIView):
    serializer_class = RegisterSerializer

    def get(self, request, *args, **kwargs):
        # Just render the empty login page
        return render(request, 'register.html')

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return render(request, 'register.html', {"message": "Registration successful."})
        return render(request, 'register.html', {'form': serializer, 'errors': serializer.errors})

class LoginAPIView(APIView):
    serializer_class = LoginSerializer

    def get(self, request, *args, **kwargs):
        # Just render the empty login page
        return render(request, 'login.html')

    def post(self, request, *args, **kwargs):
        if 'qr_image' in request.FILES:
            qr_file = request.FILES['qr_image']
            try:
                img = Image.open(qr_file).convert('RGB')
                img_np = np.array(img)
                img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

                detector = cv2.QRCodeDetector()
                data, bbox, _ = detector.detectAndDecode(img_cv)

                if data:
                    return redirect(data)  # Redirect to decoded URL
                else:
                    return render(request, 'login.html', {'qr_error': "Could not decode QR code."})
            except Exception as e:
                return render(request, 'login.html', {'qr_error': f"QR decoding error: {str(e)}"})

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            request.session['username'] = user.username
            request.session['refresh'] = str(serializer.validated_data['refresh'])
            request.session['access'] = str(serializer.validated_data['access'])
            request.session['user_id'] = user.id  # ✅ This is the missing line
            return redirect('/events/')

        return render(request, 'login.html', {'form': serializer, 'errors': serializer.errors})

    
class BookingCreateView(APIView):
    permission_classes = [permissions.AllowAny]  # Change if needed
    User = get_user_model()

    def get(self, request, event_id, *args, **kwargs):
        if not request.session.get('access'):
            return redirect('login')

        event = get_object_or_404(Event, id=event_id)
        user_id = request.session.get('user_id')

        bookings = []
        if user_id:
            try:
                user = self.User.objects.get(id=user_id)
                bookings = Booking.objects.filter(user=user, event__date__gt=now())
            except self.User.DoesNotExist:
                pass

        return render(request, 'booking.html', {
            'event': event,
            'user': request.session.get('username'),
            'tokens': {
                'refresh': request.session.get('refresh'),
                'access': request.session.get('access')
            },
            'bookings': bookings,
            'now': now(),
        })

    def post(self, request, event_id, *args, **kwargs):
        event = get_object_or_404(Event, id=event_id)

        user_id = request.session.get('user_id')
        if not user_id:
            return Response({"detail": "User not authenticated."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            user = self.User.objects.get(id=user_id)
        except self.User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            seats_booked = int(request.POST.get('seats_booked', 0))
        except ValueError:
            seats_booked = 0

        if seats_booked <= 0:
            bookings = Booking.objects.filter(user=user, event__date__gt=now())
            return render(request, 'booking.html', {
                'event': event,
                'error': "Please enter a valid number of seats.",
                'user': request.session.get('username'),
                'tokens': {
                    'refresh': request.session.get('refresh'),
                    'access': request.session.get('access')
                },
                'bookings': bookings,
                'now': now(),
            })

        data = {
            'event': event.id,
            'seats_booked': seats_booked
        }

        serializer = BookingSerializer(data=data, context={'user': user})
        if serializer.is_valid():
            booking = serializer.save()

            send_booking_email(
                to_email=booking.user.email,
                event=booking.event,
                seats=booking.seats_booked,
                qr_path=booking.qr_code.path
            )

            bookings = Booking.objects.filter(user=user, event__date__gt=now())
            return render(request, 'booking.html', {
                'event': event,
                'success': f"{booking.seats_booked} seat(s) booked successfully!",
                'user': request.session.get('username'),
                'tokens': {
                    'refresh': request.session.get('refresh'),
                    'access': request.session.get('access')
                },
                'bookings': bookings,
                'now': now(),
            })

        bookings = Booking.objects.filter(user=user, event__date__gt=now())
        return render(request, 'booking.html', {
            'event': event,
            'errors': serializer.errors,
            'user': request.session.get('username'),
            'tokens': {
                'refresh': request.session.get('refresh'),
                'access': request.session.get('access')
            },
            'bookings': bookings,
            'now': now(),
        })

    

class QrBookingCreateView(APIView):
    serializer_class = QrBookingSerializer

    def get_serializer_context(self):
        return {"request": self.request}

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context=self.get_serializer_context())
        
        if serializer.is_valid():
            booking = serializer.save()
            return Response(self.serializer_class(booking).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

