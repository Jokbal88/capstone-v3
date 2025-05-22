import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Creates an initial superuser with a specified username and password from environment variables.'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        username = os.environ.get('INITIAL_SUPERUSER_USERNAME')
        password = os.environ.get('INITIAL_SUPERUSER_PASSWORD')
        email = os.environ.get('INITIAL_SUPERUSER_EMAIL', '') # Email is required but can be empty

        if not username or not password:
            self.stdout.write(self.style.ERROR('INITIAL_SUPERUSER_USERNAME and INITIAL_SUPERUSER_PASSWORD environment variables must be set.'))
            return

        if not User.objects.filter(username=username).exists():
            self.stdout.write('Creating superuser...')
            try:
                user = User.objects.create_superuser(username=username, email=email, password=password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Superuser \'{username}\' created successfully.'))
            except Exception as e:
                 self.stdout.write(self.style.ERROR(f'Error creating superuser: {e}'))
        else:
            self.stdout.write(self.style.WARNING(f'Superuser \'{username}\' already exists.'))
            # Optional: Update password if needed, but let's keep it simple for now
            # user = User.objects.get(username=username)
            # user.set_password(password)
            # user.save()
            # self.stdout.write(self.style.SUCCESS(f'Superuser \'{username}\' password updated successfully.')) 