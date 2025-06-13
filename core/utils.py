import cv2
import numpy as np
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from email.mime.image import MIMEImage
from email.utils import make_msgid
import os

def decode_qr_from_cv2(image_bytes):
    """Decodes QR image using OpenCV and returns full text"""
    npimg = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(img)
    return data.strip() if data else None


def extract_booking_id_from_text(qr_text):
    """
    Extracts the Booking ID from a formatted QR text like:
    'Booking ID: 38\nUser: arun\nEvent: Intro to Python Workshop\nSeats: 2'
    """
    for line in qr_text.split('\n'):
        if line.strip().lower().startswith('booking id:'):
            try:
                return int(line.split(':')[1].strip())
            except (IndexError, ValueError):
                return None
    return None


def send_booking_email(to_email, event, seats, qr_path):
    subject = f'Your Booking for {event.name} is Confirmed!'
    total_price = event.price * seats
    event_datetime = event.date.strftime('%A, %d %B %Y | %I:%M %p')

    # Generate CIDs
    qr_cid = make_msgid(domain='eventmail.local')[1:-1]
    event_cid = make_msgid(domain='eventmail.local')[1:-1]

    # Plain Text Body
    text_body = (
        f"Your booking for {event.name} is confirmed!\n\n"
        f"Date & Time: {event_datetime}\n"
        f"Location: {event.location}\n"
        f"Organizer: {event.organizer}\n"
        f"Seats Booked: {seats}\n"
        f"Total Price: ₹{total_price:.2f}\n\n"
        f"QR code and event image are attached.\n"
    )

    # HTML Body using CID for images
    html_body = f"""
    <html>
    <body style="margin:0; padding:0; background-color:#121212; font-family:Arial,sans-serif; color:#f0f0f0;">
    <div style="max-width:600px; margin:20px auto; background:linear-gradient(145deg,#1e1e1e,#2a2a2a); border:1px solid #3a3a3a; border-radius:20px; box-shadow:0 8px 20px rgba(0,0,0,0.5); padding:20px;">

        <h2 style="text-align:center; color:#27ae60;">🎟️ Booking Confirmed</h2>
        <p style="text-align:center; color:#ccc;">Your booking for <strong>{event.name}</strong> is confirmed!</p>

        {'<div style="text-align:center;"><img src="cid:{}" style="width:100%; max-width:300px; border-radius:12px; object-fit:cover;" alt="Event Image" /></div>'.format(event_cid) if event.image else ''}

        <table style="width:100%; font-size:14px; margin-top:20px;">
            <tr><td><strong>Date & Time:</strong></td><td>{event_datetime}</td></tr>
            <tr><td><strong>Location:</strong></td><td>{event.location or 'To be announced'}</td></tr>
            <tr><td><strong>Organizer:</strong></td><td>{event.organizer or 'Event Team'}</td></tr>
            <tr><td><strong>Seats Booked:</strong></td><td>{seats}</td></tr>
            <tr><td><strong>Total Price:</strong></td><td>₹{total_price:.2f}</td></tr>
        </table>

        <div style="margin-top:20px;">
            <p><strong>Event Description:</strong></p>
            <p style="background-color:#1b1b1b; padding:10px 15px; border-left:4px solid #27ae60; color:#bbbbbb;">
                {event.description or 'No additional description provided.'}
            </p>
        </div>

        <div style="text-align:center; margin-top:20px;">
            <p>📎 Present this QR code at the event venue:</p>
            <img src="cid:{qr_cid}" style="width:120px; height:120px; border-radius:10px; border:1px solid #444;" alt="QR Code" />
        </div>

        <p style="text-align:center; font-size:13px; color:#888; margin-top:30px;">
            This is an automated email. Please do not reply.<br>
            Regards, <strong>{event.organizer or 'Event Team'}</strong>
        </p>

    </div>
    </body>
    </html>
    """

    try:
        email = EmailMultiAlternatives(subject, text_body, settings.EMAIL_HOST_USER, [to_email])
        email.attach_alternative(html_body, "text/html")

        # Attach inline QR image
        if os.path.exists(qr_path):
            with open(qr_path, 'rb') as f:
                qr_image = MIMEImage(f.read())
                qr_image.add_header('Content-ID', f'<{qr_cid}>')
                qr_image.add_header('Content-Disposition', 'inline', filename='qr.png')
                email.attach(qr_image)

        # Attach inline Event image
        if event.image and hasattr(event.image, 'path') and os.path.exists(event.image.path):
            with open(event.image.path, 'rb') as f:
                event_image = MIMEImage(f.read())
                event_image.add_header('Content-ID', f'<{event_cid}>')
                event_image.add_header('Content-Disposition', 'inline', filename='event.jpg')
                email.attach(event_image)

        # Optional: Attach as files too
        # if os.path.exists(qr_path):
        #     email.attach_file(qr_path)
        # if event.image and hasattr(event.image, 'path') and os.path.exists(event.image.path):
        #     email.attach_file(event.image.path)

        email.send()
        print("Email sent successfully with visible inline images!")
    except Exception as e:
        print("Error sending email:", e)