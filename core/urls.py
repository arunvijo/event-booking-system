from django.urls import path
from .views import *

urlpatterns = [
    path('', LoginAPIView.as_view(), name='home'),  # Root URL renders login page
    path('events/', EventAPIView.as_view(), name='events'),
    path('events/<int:pk>/', EventAPIView.as_view(), name='event_detail'),
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('book/<int:event_id>/', BookingCreateView.as_view(), name='book_event'),
    path('generate-qr/', QrBookingCreateView.as_view(), name='generate_qr'),
    path('logout/', logout_view, name='logout'),
]
