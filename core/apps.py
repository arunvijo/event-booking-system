from django.apps import AppConfig
from django.contrib.auth import get_user_model
from django.db.utils import OperationalError, ProgrammingError


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        try:
            User = get_user_model()
            if not User.objects.filter(username='admin').exists():
                User.objects.create_superuser(
                    username='admin',
                    email='admin@vvdn.com',
                    password='admin123'
                )
                print("✔ Superuser created: admin / admin123")
            else:
                print("ℹ Superuser already exists.")
        except (OperationalError, ProgrammingError):
            # Happens when database is not ready yet
            print("⚠ Skipped superuser creation - DB not ready.")
