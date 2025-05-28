from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from main.models import Profile, Faculty

class Command(BaseCommand):
    help = 'Creates Faculty instances for existing faculty users'

    def handle(self, *args, **kwargs):
        # Get all users with faculty role in their profile
        faculty_profiles = Profile.objects.filter(role='Faculty')
        
        for profile in faculty_profiles:
            # Check if Faculty instance already exists
            if not hasattr(profile.user, 'faculty'):
                # Create Faculty instance
                Faculty.objects.create(
                    user=profile.user,
                    department='Default Department',  # You can update this later
                    position='Faculty Member'  # You can update this later
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Created Faculty profile for {profile.user.email}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Faculty profile already exists for {profile.user.email}')
                ) 