# Use official Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies (for WeasyPrint and others)
RUN apt-get update && apt-get install -y \
  build-essential \
  libpq-dev \
  gcc \
  libcairo2 \
  libpango-1.0-0 \
  libpangocairo-1.0-0 \
  libgdk-pixbuf2.0-0 \
  libffi-dev \
  libjpeg-dev \
  zlib1g-dev \
  libgl1 \
  libglib2.0-0 \
  libsm6 \
  libxrender1 \
  libxext6 \
  shared-mime-info \
  fonts-liberation \
  fonts-dejavu \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8080

# Start the Gunicorn server
CMD gunicorn event_booking.wsgi:application --bind 0.0.0.0:$PORT
