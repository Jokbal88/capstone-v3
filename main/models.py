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
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def is_otp_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(minutes=5)

    def __str__(self):
        return f"Verification for {self.user.email}"

class Faculty(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    faculty_id = models.CharField(max_length=7, unique=True, null=True, blank=True)
    department = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    sex = models.CharField(max_length=1, choices=Student.GENDER_CHOICES, null=True, blank=True)
    middlename = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.faculty_id}) - {self.position}"

class Profile(models.Model):
    ROLE_CHOICES = (
        ('Student', 'Student'),
        ('Faculty', 'Faculty'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='Student')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role}"
