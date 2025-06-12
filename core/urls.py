from django.urls import path
from .views import *
from . import views


urlpatterns = [
    path('', LoginAPIView.as_view(), name='home'),  # Root URL renders login page
    path('events/', EventAPIView.as_view(), name='events'),
    path('events/<int:pk>/', EventAPIView.as_view(), name='event_detail'),
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('book/<int:event_id>/', BookingCreateView.as_view(), name='book_event'),
    path('generate-qr/', QrBookingCreateView.as_view(), name='generate_qr'),
    path('logout/', logout_view, name='logout'),
    path('admin-panel/', views.admin_login, name='admin_login'),
    path('admin-panel/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin-panel/add/', views.admin_add_event, name='admin_add_event'),
    path('admin-panel/edit/<int:pk>/', views.admin_edit_event, name='admin_edit_event'),
    path('api/events/<int:pk>/', EventDetailAPIView.as_view(), name='event_detail_api'),
]
