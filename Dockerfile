# Use official Python image
FROM python:3.10-slim

# Set environment vars
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files
COPY . .

# Collect static files (optional if you're serving via Django)
RUN python manage.py collectstatic --noinput

# Start server with gunicorn
CMD gunicorn event_booking.wsgi:application --bind 0.0.0.0:$PORT
