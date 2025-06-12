from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken



class EventSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = '__all__'

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    def validate(self, data):
        name = data.get('name', getattr(self.instance, 'name', None))
        date = data.get('date', getattr(self.instance, 'date', None))
        location = data.get('location', getattr(self.instance, 'location', None))

        qs = Event.objects.filter(name=name, date=date, location=location)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError("An event with the same name, date, and location already exists.")

        return data


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id','first_name','last_name','email','username','password','confirm_password',]

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user
    
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid username or password")
        
        refresh = RefreshToken.for_user(user)
        data['user'] = user
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        return data
    
class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'user', 'event', 'seats_booked', 'booking_time']
        read_only_fields = ['id', 'booking_time', 'user']

    def validate(self, data):
        event = data['event']
        seats_requested = data['seats_booked']

        if seats_requested <= 0:
            raise serializers.ValidationError("Seats booked must be greater than zero.")

        if event.available_seats < seats_requested:
            raise serializers.ValidationError(f"Only {event.available_seats} seats are available.")
        
        return data

    def create(self, validated_data):
        event = validated_data['event']
        seats_requested = validated_data['seats_booked']

        # Update event's available seats
        event.available_seats -= seats_requested
        event.save()

        user = self.context['user']  # ✅ Use user from context

        booking = Booking.objects.create(user=user, **validated_data)
        return booking


    
class QrBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = QrBooking
        fields = ['id', 'name', 'event', 'seats_booked', 'booking_time']
        read_only_fields = ['id', 'booking_time']

    def validate(self, data):
        event = data['event']
        seats_requested = data['seats_booked']

        if seats_requested <= 0:
            raise serializers.ValidationError("Seats booked must be greater than zero.")

        if event.available_seats < seats_requested:
            raise serializers.ValidationError(f"Only {event.available_seats} seats are available.")
        
        return data

    def create(self, validated_data):
        event = validated_data['event']
        seats_requested = validated_data['seats_booked']

        event.available_seats -= seats_requested
        event.save()

        booking = QrBooking.objects.create(**validated_data)
        return booking

    