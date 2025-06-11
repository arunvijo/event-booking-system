import os
import socket
import qrcode
from django.conf import settings
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Generates a static QR code pointing to /generate-qr/'

    def handle(self, *args, **kwargs):
        def get_local_ip():
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
            finally:
                s.close()
            return ip

        local_ip = get_local_ip()
        target_url = f"http://{local_ip}:8000/generate-qr/"

        qr_folder = os.path.join(settings.MEDIA_ROOT, "qr_codes")
        os.makedirs(qr_folder, exist_ok=True)

        qr_path = os.path.join(qr_folder, "static_qr.png")
        qr_img = qrcode.make(target_url)
        qr_img.save(qr_path)

        self.stdout.write(self.style.SUCCESS(f"QR code generated and saved to: {qr_path}"))
