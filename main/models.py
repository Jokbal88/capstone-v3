from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class Student(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]

    student_id = models.CharField(max_length=7, unique=True)
    lrn = models.CharField(max_length=12, unique=True)
    lastname = models.CharField(max_length=100)
    firstname = models.CharField(max_length=100)
    middlename = models.CharField(max_length=100, blank=True)
    degree = models.CharField(max_length=100)
    year_level = models.IntegerField()
    sex = models.CharField(max_length=1, choices=GENDER_CHOICES)
    email = models.EmailField(unique=True)
    contact_number = models.CharField(max_length=11)

    class Meta:
        ordering = ['lastname', 'firstname']

    def __str__(self):
        return f"{self.student_id} - {self.lastname}, {self.firstname}"

class EmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_verification')
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    
    def is_token_expired(self):
        # Token expires after 24 hours
        return (timezone.now() - self.created_at).total_seconds() > 86400
    
    def __str__(self):
        return f"Verification for {self.user.email}"
