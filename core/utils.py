import cv2
import numpy as np

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
