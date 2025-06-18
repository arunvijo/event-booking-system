# Use official Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies (for psycopg2 & Pillow etc.)
RUN apt-get update \
  && apt-get install -y build-essential libpq-dev gcc musl-dev libjpeg-dev zlib1g-dev \
  && apt-get clean

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

RUN apt-get update && apt-get install -y libgl1


# Copy project files
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8080

# Start the Gunicorn server
CMD gunicorn event_booking.wsgi:application --bind 0.0.0.0:$PORT
