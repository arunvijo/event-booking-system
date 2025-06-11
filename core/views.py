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
from django.contrib.auth import get_user_model


# Create your methods here.
def send_booking_email(to_email, event, seats, qr_path):
    """
    Sends a booking confirmation email with event details, QR code, and event image.
    """
    subject = f'🎟️ Your Booking for {event.name} is Confirmed!'

    body = (
        f"Hello,\n\n"
        f"Thank you for booking *{seats} seat(s)* for the event **{event.name}**.\n\n"
        f"Here are your event details:\n"
        f"📅 Date & Time: {event.date.strftime('%A, %d %B %Y at %I:%M %p')}\n"
        f"📍 Location: {event.location or 'To be announced'}\n"
        f"👤 Organizer: {event.organizer or 'Event Team'}\n"
        f"💺 Seats Booked: {seats}\n"
        f"💰 Total Price: ₹{event.price * seats:.2f}\n\n"
        f"📝 Description:\n{event.description or 'No additional details provided.'}\n\n"
        f"🎫 Your QR code ticket is attached to this email.\n"
        f"🖼️ We’ve also attached the event poster/image for your reference.\n\n"
        f"Looking forward to seeing you there!\n\n"
        f"Regards,\n"
        f"{event.organizer or 'Event Team'}"
    )

    try:
        email = EmailMessage(subject, body, settings.EMAIL_HOST_USER, [to_email])

        # Attach QR code file
        if os.path.exists(qr_path):
            email.attach_file(qr_path)

        # Attach event image if available
        if event.image and hasattr(event.image, 'path') and os.path.exists(event.image.path):
            email.attach_file(event.image.path)

        email.send()
        print("Email sent successfully with QR code and event image!")
    except Exception as e:
        print("Error sending email with attachments:", e)


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
            request.session['user_id'] = user.id  # ✅ This is the missing line
            return redirect('/events/')

        return render(request, 'login.html', {'form': serializer, 'errors': serializer.errors})

    

class BookingCreateView(APIView):
    permission_classes = [permissions.AllowAny]  # Change if needed

    def get(self, request, event_id, *args, **kwargs):
        if not request.session.get('access'):
            return redirect('login')  # Redirect to login if no access token

        event = get_object_or_404(Event, id=event_id)
        return render(request, 'booking.html', {
            'event': event,
            'user': request.session.get('username'),
            'tokens': {
                'refresh': request.session.get('refresh'),
                'access': request.session.get('access')
            }
        })

    User = get_user_model()

    def post(self, request, event_id, *args, **kwargs):
        event = get_object_or_404(Event, id=event_id)

        user_id = request.session.get('user_id')
        if not user_id:
            return Response({"detail": "User not authenticated."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            seats_booked = int(request.POST.get('seats_booked', 0))
        except ValueError:
            seats_booked = 0

        if seats_booked <= 0:
            return render(request, 'booking.html', {
                'event': event,
                'error': "Please enter a valid number of seats.",
                'user': request.session.get('username'),
                'tokens': {
                    'refresh': request.session.get('refresh'),
                    'access': request.session.get('access')
                }
            })

        data = {
            'event': event.id,
            'seats_booked': seats_booked
        }

        # ✅ Pass the user instance in the context
        serializer = BookingSerializer(data=data, context={'user': user})
        if serializer.is_valid():
            booking = serializer.save()

            send_booking_email(
                to_email=booking.user.email,
                event=booking.event,
                seats=booking.seats_booked,
                qr_path=booking.qr_code.path
            )


            return render(request, 'booking.html', {
                'event': event,
                'success': f"{booking.seats_booked} seat(s) booked successfully!",
                'user': request.session.get('username'),
                'tokens': {
                    'refresh': request.session.get('refresh'),
                    'access': request.session.get('access')
                }
            })

        return render(request, 'booking.html', {
            'event': event,
            'errors': serializer.errors,
            'user': request.session.get('username'),
            'tokens': {
                'refresh': request.session.get('refresh'),
                'access': request.session.get('access')
            }
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

