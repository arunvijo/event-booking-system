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
from PIL import Image
import numpy as np
import cv2



# Create your methods here.
def send_booking_email(to_email, event_name, seats, qr_path):
    subject = 'Your Booking is Confirmed!'
    body = (
        f'Thank you for booking {seats} seat(s) for the event: {event_name}.\n\n'
        'Please find your QR code ticket attached.'
    )

    try:
        email = EmailMessage(subject, body, settings.EMAIL_HOST_USER, [to_email])
        
        if os.path.exists(qr_path):
            email.attach_file(qr_path)

        email.send()
        print("Email sent successfully with QR code!")
    except Exception as e:
        print("Error sending email with QR code:", e)

def logout_view(request):
    request.session.flush()
    messages.success(request, "You have been logged out successfully.")
    return redirect('login') 

# Create your views here.
class EventAPIView(APIView):
   def get(self, request, pk=None):
    if pk:
        # Detail view logic
        event = get_object_or_404(Event, pk=pk)
        serializer = EventSerializer(event)
        return render(request, 'events.html', {
            'event': serializer.data,  # Single event object for detail view
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
    # elif sort_by == 'price':
    #     events = events.order_by('price')

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
       serializer = EventSerializer(data=request.data)
       if serializer.is_valid():
           serializer.save()
           return Response({"message": "Event created successfully"}, status=status.HTTP_201_CREATED)
       return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


   def put(self, request, pk):
       event = get_object_or_404(Event, pk=pk)
       serializer = EventSerializer(event, data=request.data, partial=True)
       if serializer.is_valid():
           serializer.save()
           return Response({"message": "Event updated successfully"})
       return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
   
   def delete(self, request, pk):
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
            return redirect('/events/')
        return render(request, 'login.html', {'form': serializer, 'errors': serializer.errors})

    

class BookingCreateView(APIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def post(self, request, event_id, *args, **kwargs):
        event = get_object_or_404(Event, id=event_id)
        data = request.data.copy()
        data['event'] = event.id
        data['user'] = request.user.id 

        serializer = self.serializer_class(data=data, context=self.get_serializer_context())
        if serializer.is_valid():
            booking = serializer.save()

            user_email = booking.user.email
            event_name = booking.event.name
            seats = booking.seats_booked
            qr_path = booking.qr_code 
            send_booking_email(user_email, event_name, seats, qr_path.path)

            return Response(self.serializer_class(booking).data, status=status.HTTP_201_CREATED)

        return Response("Required No. of seats not available", status=status.HTTP_400_BAD_REQUEST)
    

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

