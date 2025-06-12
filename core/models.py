from django.db import models
from django.contrib.auth.models import User
import qrcode
from io import BytesIO
from django.core.files import File

from django.db import models
from django.core.validators import MinValueValidator

class Event(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateTimeField()
    description = models.TextField(blank=True, default='')
    total_seats = models.PositiveIntegerField(default=0)
    available_seats = models.PositiveIntegerField(default=0)
    location = models.CharField(max_length=255, blank=True, default='')
    organizer = models.CharField(max_length=100, blank=True, default='')
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        upload_to='event_images/',
        blank=True,
        null=True,
        help_text="Upload an image for this event"
    )

    def __str__(self):
        return self.name
    
class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey('Event', on_delete=models.CASCADE)
    seats_booked = models.PositiveIntegerField()
    booking_time = models.DateTimeField(auto_now_add=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True)
    is_checked_in = models.BooleanField(default=False)

    def generate_qr_code(self):
        data = (
            f'Booking ID: {self.id}\n'
            f'User: {self.user.username}\n'
            f'Event: {self.event.name}\n'
            f'Seats: {self.seats_booked}'
        )
        qr_img = qrcode.make(data)
        buffer = BytesIO()
        qr_img.save(buffer, format='PNG')
        filename = f'booking_{self.id}_qr.png'
        self.qr_code.save(filename, File(buffer), save=False)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new:
            super().save(*args, **kwargs)  # First save to get ID
            self.generate_qr_code()        # Generate QR after ID is available
            super().save(update_fields=['qr_code'])  # Save only the QR field
        else:
            super().save(*args, **kwargs)  # Normal update for non-new objects

    def __str__(self):
        return f"{self.user.username} - {self.event.name}"
    
class QrBooking(models.Model):
    name = models.CharField(max_length=100)
    event = models.ForeignKey('Event', on_delete=models.CASCADE)
    seats_booked = models.PositiveIntegerField()
    booking_time = models.DateTimeField(auto_now_add=True)