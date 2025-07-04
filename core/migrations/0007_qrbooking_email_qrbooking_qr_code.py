# Generated by Django 5.2.1 on 2025-06-13 06:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_booking_is_checked_in"),
    ]

    operations = [
        migrations.AddField(
            model_name="qrbooking",
            name="email",
            field=models.EmailField(default="default@example.com", max_length=254),
        ),
        migrations.AddField(
            model_name="qrbooking",
            name="qr_code",
            field=models.ImageField(blank=True, null=True, upload_to="qr_codes/"),
        ),
    ]
