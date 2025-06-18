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
    path('admin-panel/event/<int:event_id>/details/', views.admin_event_details, name='admin_event_details'),
    path('admin-panel/booking/<int:booking_id>/delete/', views.admin_delete_booking, name='admin_delete_booking'),
    path('admin-panel/event/<int:event_id>/checkin/', views.admin_checkin_qr, name='admin_checkin_qr'),
    path('admin-panel/event/<int:event_id>/download/csv/', views.download_bookings_csv, name='download_bookings_csv'),
    path('admin-panel/event/<int:event_id>/download/pdf/', views.download_bookings_pdf, name='download_bookings_pdf'),
    path('run-migrations/', RunMigrationsView.as_view()),
]
