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
import csv

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

from django.views.decorators.http import require_http_methods
from django.http import HttpResponseNotAllowed
import qrcode
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
import cv2
import numpy as np

# core/views.py

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib import messages
from core.models import Event, Booking
from core.utils import decode_qr_from_cv2
import cv2
import numpy as np

from core.utils import decode_qr_from_cv2, extract_booking_id_from_text

from .utils import send_booking_email  

from django.contrib import messages



def download_bookings_csv(request, event_id):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="event_{event_id}_bookings.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name/Username', 'Seats Booked', 'Booking Time', 'Checked In'])

    bookings = Booking.objects.filter(event_id=event_id)
    qr_bookings = QrBooking.objects.filter(event_id=event_id)

    for b in bookings:
        writer.writerow([b.user.username, b.seats_booked, b.booking_time, 'Yes' if b.is_checked_in else 'No'])

    for q in qr_bookings:
        writer.writerow([q.name, q.seats_booked, q.booking_time, 'Yes' if q.is_checked_in else 'No'])

    return response

from django.template.loader import render_to_string
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas



def download_bookings_pdf(request, event_id):
    bookings = Booking.objects.filter(event_id=event_id)
    qr_bookings = QrBooking.objects.filter(event_id=event_id)
    event = Event.objects.get(id=event_id)

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4
    y = height - inch

    p.setFont("Helvetica-Bold", 16)
    p.drawString(inch, y, f"Event: {event.name}")
    y -= 20

    p.setFont("Helvetica", 12)
    p.drawString(inch, y, f"Date: {event.date}")
    y -= 20
    p.drawString(inch, y, f"Location: {event.location}")
    y -= 40

    p.setFont("Helvetica-Bold", 14)
    p.drawString(inch, y, "Bookings:")
    y -= 20

    p.setFont("Helvetica", 12)
    for booking in bookings:
        if y < inch:
            p.showPage()
            y = height - inch
        p.drawString(inch, y, f"{booking.user.username} - {booking.seats_booked} seat(s)")
        y -= 15

    y -= 20
    p.setFont("Helvetica-Bold", 14)
    p.drawString(inch, y, "QR Bookings:")
    y -= 20

    p.setFont("Helvetica", 12)
    for qr_booking in qr_bookings:
        if y < inch:
            p.showPage()
            y = height - inch
        p.drawString(inch, y, f"{qr_booking.name} - {qr_booking.seats_booked} seat(s)")
        y -= 15

    p.save()
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="event_{event_id}_bookings.pdf"'
    return response

@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(["POST"])
def admin_checkin_qr(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    booking = None
    message = ''
    success = False

    if 'qr_text' in request.POST:
        qr_text = request.POST.get('qr_text')
        booking_id = extract_booking_id_from_text(qr_text)
        if booking_id:
            booking = Booking.objects.filter(id=booking_id, event=event).first()
            if not booking:
                booking = QrBooking.objects.filter(id=booking_id, event=event).first()

    elif 'qr_image' in request.FILES:
        image_file = request.FILES['qr_image']
        image_bytes = image_file.read()
        qr_text = decode_qr_from_cv2(image_bytes)
        booking_id = extract_booking_id_from_text(qr_text) if qr_text else None
        if booking_id:
            booking = Booking.objects.filter(id=booking_id, event=event).first()
            if not booking:
                booking = QrBooking.objects.filter(id=booking_id, event=event).first()

    if booking:
        if booking.is_checked_in:
            message = f"{getattr(booking, 'user', getattr(booking, 'name', 'User'))} has already checked in."
        else:
            booking.is_checked_in = True
            booking.save()
            message = f"{getattr(booking, 'user', getattr(booking, 'name', 'User'))} checked in successfully."
        success = True
    else:
        message = "Invalid or unrecognized QR code."

    request.session['checkin_result'] = {
        'message': message,
        'success': success
    }

    return redirect('admin_event_details', event_id=event_id)




def admin_event_details(request, event_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('admin_login')

    event = get_object_or_404(Event, id=event_id)
    bookings = Booking.objects.filter(event=event).select_related('user')
    qr_bookings = QrBooking.objects.filter(event=event)

    total_checkins = (
        bookings.filter(is_checked_in=True).count() +
        qr_bookings.filter(is_checked_in=True).count()
    )

    checkin_result = request.session.pop('checkin_result', None)

    return render(request, 'admin/event_details.html', {
        'event': event,
        'bookings': bookings,
        'qr_bookings': qr_bookings,
        'total_checkins': total_checkins,
        'checkin_result': checkin_result,
    })


@require_http_methods(["POST"])
def admin_delete_booking(request, booking_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('admin_login')

    booking = get_object_or_404(Booking, id=booking_id)
    booking.delete()
    messages.success(request, "Booking deleted successfully.")
    return redirect('admin_event_details', event_id=booking.event.id)


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

    # Seats booked per event
    seats_per_event = []
    for event in events:
        booked = Booking.objects.filter(event=event).aggregate(total=Sum('seats_booked'))['total'] or 0
        seats_per_event.append({'name': event.name, 'booked': booked})

    # Check-in data per event
    checkin_data = []
    for event in events:
        checked_in = QrBooking.objects.filter(event=event, is_checked_in=True).count()
        checkin_data.append({'name': event.name, 'checked_in': checked_in})

    return render(request, 'admin/dashboard.html', {
        'events': events,
        'total_events': total_events,
        'total_bookings': total_bookings,
        'total_seats_booked': total_seats_booked,
        'total_available_seats': total_available_seats,
        'bookings_over_time': json.dumps(bookings_over_time),
        'peak_hours': json.dumps(peak_hours),
        'seats_per_event': json.dumps(seats_per_event),
        'checkin_data': json.dumps(checkin_data),
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
        serializer = EventSerializer(data=request.POST, files=request.FILES, context={'request': request})
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
        serializer = EventSerializer(event, data=request.POST, files=request.FILES, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return redirect('admin_dashboard')
        else:
            return render(request, 'admin/edit_event.html', {'errors': serializer.errors, 'event': serializer.data})
    else:
        serializer = EventSerializer(event, context={'request': request})
        return render(request, 'admin/edit_event.html', {'event': serializer.data})




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
            serializer = EventSerializer(event, context={'request': request})
            return render(request, 'events.html', {
                'event': serializer.data,
                'user': request.session.get('username'),
                'tokens': {
                    'refresh': request.session.get('refresh'),
                    'access': request.session.get('access')
                }
            })

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
        elif sort_by == 'price':
            events = events.order_by('price')

        serializer = EventSerializer(events, many=True, context={'request': request})
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
        # if not request.user or not request.user.is_authenticated or not request.user.is_superuser:
        #     return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

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

    def get(self, request, *args, **kwargs):
        events = Event.objects.all().order_by('date')
        return render(request, 'qr_booking.html', {'events': events})

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context=self.get_serializer_context())

        if serializer.is_valid():
            booking = serializer.save()
            return Response(self.serializer_class(booking).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


