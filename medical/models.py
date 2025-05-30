from django.db import models
import os
from django.contrib.auth.models import User
from main.models import Student, Faculty
from django.utils import timezone

# Helper function for profile picture upload path
def profile_picture_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/medical/<lastname>_<firstname>/profile_picture/<filename>
    # Updated to use user's username or ID for path
    user_identifier = instance.user.username or instance.user.id # Use username or ID as identifier
    return os.path.join('medical', f'{user_identifier}', 'profile_picture', filename)

# Create your models here.
class Student(models.Model):
    student_id = models.CharField(max_length=100, primary_key=True)
    lrn = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    firstname = models.CharField(max_length=100)
    middlename = models.CharField(max_length=100, null=True, blank=True)
    degree = models.CharField(max_length=100)
    year_level = models.PositiveIntegerField()
    sex = models.CharField(max_length=6)
    email = models.EmailField()
    contact_number = models.CharField(max_length=15)
    
    def __str__(self):
        return f"{self.lastname}, {self.firstname}"

class Patient(models.Model):
    # Link Patient to the User model instead of Student
    # Make nullable initially for migration purposes
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    # Add profile picture field
    profile_picture = models.ImageField(upload_to=profile_picture_path, null=True, blank=True)

    birth_date = models.CharField(max_length=100)
    # Make age nullable for initial patient creation during registration
    age = models.PositiveIntegerField(null=True, blank=True)
    # Make weight nullable for initial patient creation during registration
    weight = models.FloatField(null=True, blank=True)
    # Make height nullable for initial patient creation during registration
    height = models.FloatField(null=True, blank=True)
    # Make bloodtype nullable for initial patient creation during registration
    bloodtype = models.CharField(max_length=20, null=True, blank=True)
    # Make allergies nullable for initial patient creation during registration
    allergies = models.CharField(max_length=100, null=True, blank=True)
    # Make medications nullable for initial patient creation during registration
    medications = models.CharField(max_length=100, null=True, blank=True)
    # Make home_address nullable for initial patient creation during registration
    home_address = models.CharField(max_length=100, null=True, blank=True)
    # Make city nullable for initial patient creation during registration
    city = models.CharField(max_length=100, null=True, blank=True)
    # Make state_province nullable for initial patient creation during registration
    state_province = models.CharField(max_length=100, null=True, blank=True)
    # Make postal_zipcode nullable for initial patient creation during registration
    postal_zipcode = models.CharField(max_length=20, null=True, blank=True)
    # Make country nullable for initial patient creation during registration
    country = models.CharField(max_length=100, null=True, blank=True)
    # Make nationality nullable for initial patient creation during registration
    nationality = models.CharField(max_length=100, null=True, blank=True)
    # Make civil_status nullable for initial patient creation during registration
    civil_status = models.CharField(max_length=20, null=True, blank=True)
    # Make religion nullable for initial patient creation during registration
    religion = models.CharField(max_length=50, null=True, blank=True)
    # Make number_of_children nullable for initial patient creation during registration
    number_of_children = models.PositiveIntegerField(null=True, blank=True)
    # Make academic_year nullable for initial patient creation during registration
    academic_year = models.CharField(max_length=20, null=True, blank=True)
    # Make section nullable for initial patient creation during registration
    section = models.CharField(max_length=20, null=True, blank=True)
    # Make parent_guardian nullable for initial patient creation during registration
    parent_guardian = models.CharField(max_length=100, null=True, blank=True)
    # Make parent_guardian_contact_number nullable for initial patient creation during registration
    parent_guardian_contact_number = models.CharField(max_length=15, null=True, blank=True)
    # Make examination nullable for initial patient creation during registration
    examination = models.OneToOneField('PhysicalExamination', on_delete=models.CASCADE, related_name='patient_for_examination', null=True, blank=True)

    def __str__(self):
        # Updated to use user's information
        return f"Patient Record for {self.user.get_full_name() or self.user.username}"

class PhysicalExamination(models.Model):
    # Keep link to Patient, which is now linked to User
    # Make nullable initially for migration purposes
    patient = models.OneToOneField('Patient', on_delete=models.CASCADE, related_name='physical_examination', null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_of_physical_examination = models.CharField(max_length=100)
    
    def __str__(self):
        # Updated to use patient's user information
        return f"Physical Exam - {self.patient.user.get_full_name() or self.patient.user.username}"

class MedicalHistory(models.Model):
    examination = models.OneToOneField(PhysicalExamination, on_delete=models.CASCADE)
    tuberculosis = models.BooleanField(default=False)
    hypertension = models.BooleanField(default=False)
    heart_disease = models.BooleanField(default=False)
    hernia = models.BooleanField(default=False)
    epilepsy = models.BooleanField(default=False)
    peptic_ulcer = models.BooleanField(default=False)
    kidney_disease = models.BooleanField(default=False)
    asthma = models.BooleanField(default=False)
    insomnia = models.BooleanField(default=False)
    malaria = models.BooleanField(default=False)
    venereal_disease = models.BooleanField(default=False)
    allergic_reaction = models.BooleanField(default=False)
    nervous_breakdown = models.BooleanField(default=False)
    jaundice = models.BooleanField(default=False)
    others = models.CharField(max_length=100, null=True, blank=True)
    no_history = models.BooleanField(default=False)
    hospital_admission = models.CharField(max_length=255, null=True, blank=True)
    medications = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        # Updated to use examination's patient's user information
        return f"Medical history of {self.examination.patient.user.get_full_name() or self.examination.patient.user.username}"

class FamilyMedicalHistory(models.Model):
    examination = models.OneToOneField(PhysicalExamination, on_delete=models.CASCADE)
    hypertension = models.BooleanField(default=False)
    asthma = models.BooleanField(default=False)
    cancer = models.BooleanField(default=True)
    tuberculosis = models.BooleanField(default=False)
    diabetes = models.BooleanField(default=False)
    bleeding_disorder = models.BooleanField(default=False)
    epilepsy = models.BooleanField(default=False)
    mental_disorder = models.BooleanField(default=False)
    no_history = models.BooleanField(default=False)
    other_medical_history = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        # Updated to use examination's patient's user information
        return f"Family Medical History of {self.examination.patient.user.get_full_name() or self.examination.patient.user.username}"

class ObgyneHistory(models.Model):
    examination = models.OneToOneField(PhysicalExamination, on_delete=models.CASCADE)
    menarche = models.CharField(max_length=100, null=True, blank=True)
    lmp = models.CharField(max_length=100, null=True, blank=True)
    pap_smear = models.CharField(max_length=100, null=True, blank=True)
    gravida = models.CharField(max_length=10, null=True, blank=True)
    para = models.CharField(max_length=10, null=True, blank=True)
    menopause = models.CharField(max_length=100, null=True, blank=True)
    additional_history = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        # Updated to use examination's patient's user information
        return f"OB-GYNE History of {self.examination.patient.user.get_full_name() or self.examination.patient.user.username}"
    
class MedicalClearance(models.Model):
    # MedicalClearance is primary_key, linking to Patient. No direct nullability needed here,
    # but ensure reverse links are handled.
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, primary_key=True)

    def __str__(self):
        # Updated to use patient's user information
        return f"Medical clearance for {self.patient.user.get_full_name() or self.patient.user.username}"

class RiskAssessment(models.Model):
    # Keep link to Patient, which is now linked to User (via MedicalClearance)
    medical_clearance_id = models.OneToOneField(MedicalClearance, on_delete=models.CASCADE, related_name="riskassessment", null=True, blank=True)
    id = models.AutoField(primary_key=True)
    # Link to Patient, make nullable initially
    clearance = models.OneToOneField(Patient, on_delete=models.CASCADE, null=True, blank=True)
    cardiovascular_disease = models.BooleanField(default=False)
    chronic_lung_disease = models.BooleanField(default=False)
    chronic_renal_disease = models.BooleanField(default=False)
    chronic_liver_disease = models.BooleanField(default=False)
    cancer = models.BooleanField(default=False)
    autoimmune_disease = models.BooleanField(default=False)
    pwd = models.BooleanField(default=False)
    disability = models.CharField(max_length=255, blank=True)
    pwd_verified = models.BooleanField(default=False)
    pwd_verification_date = models.DateTimeField(null=True, blank=True)
    pwd_verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_pwd')

    def __str__(self):
        return f"Risk Assessment for {self.clearance}"

    class Meta:
        verbose_name = "Risk Assessment"
        verbose_name_plural = "Risk Assessments"
    
    # def pwd_path(instance, filename, field_name):
    #     return os.path.join('pwd', f'{instance.clearance.student.lastname}_{instance.clearance.student.firstname}', field_name, filename)
    
    # def pwd_idcard(instance, filename):
    #     return RiskAssessment.pwd_path(instance, filename, 'pwd_card')
    
    # pwd_id_card = models.FileField(upload_to=pwd_path, null=True, blank=True)
    
class MedicalRequirement(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    # Link to Patient, make nullable initially
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, null=True, blank=True)
    faculty = models.OneToOneField(Faculty, on_delete=models.CASCADE, null=True, blank=True)
    vaccination_type = models.CharField(max_length=50, null=True, blank=True)
    vaccinated_1st = models.BooleanField(default=False, null=True, blank=True)
    vaccinated_2nd = models.BooleanField(default=False, null=True, blank=True)
    vaccinated_booster = models.BooleanField(default=False, null=True, blank=True)

    x_ray_remarks = models.CharField(max_length=100, null=True, blank=True)
    cbc_remarks = models.CharField(max_length=100, null=True, blank=True)
    drug_test_remarks = models.CharField(max_length=100, null=True, blank=True)
    stool_examination_remarks = models.CharField(max_length=100, null=True, blank=True)

    def patient_directory_path(instance, filename, field_name):
        # Use patient's user or faculty's user for path
        if instance.patient and instance.patient.user:
            user_identifier = instance.patient.user.username or instance.patient.user.id
        elif hasattr(instance, 'faculty') and instance.faculty and instance.faculty.user:
            user_identifier = instance.faculty.user.username or instance.faculty.user.id
        else:
            user_identifier = 'unknown_user'
        return os.path.join('medical', f'{user_identifier}', field_name, filename)
    
    def chest_xray_path(instance, filename):
        return MedicalRequirement.patient_directory_path(instance, filename, 'chest_xrays')
    
    def cbc_path(instance, filename):
        return MedicalRequirement.patient_directory_path(instance, filename, 'cbc')
    
    def drug_test_path(instance, filename):
        return MedicalRequirement.patient_directory_path(instance, filename, 'drug_tests')
    
    def stool_examination_path(instance, filename):
        return MedicalRequirement.patient_directory_path(instance, filename, 'stool_exam')
    
    def pwd_id_card_path(instance, filename):
        return MedicalRequirement.patient_directory_path(instance, filename, 'pwd_card')

    chest_xray = models.FileField(upload_to=chest_xray_path)
    cbc = models.FileField(upload_to=cbc_path)
    drug_test = models.FileField(upload_to=drug_test_path)
    stool_examination = models.FileField(upload_to=stool_examination_path)
    pwd_card = models.FileField(upload_to=pwd_id_card_path, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reviewed_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        if self.patient:
            return f"Medical Requirements for {self.patient.user.get_full_name() or self.patient.user.username}"
        elif self.faculty:
            return f"Medical Requirements for Faculty {self.faculty.user.get_full_name() or self.faculty.user.username}"
        else:
            return "Medical Requirements (No patient or faculty linked)"

    # def delete(self, *args, **kwargs):
    #     self.chest_xray.delete(save=False)
    #     self.cbc.delete(save=False)
    #     self.drug_test.delete(save=False)
    #     self.stool_examination.delete(save=False)
    #     super().delete(*args, **kwargs)

class EligibilityForm(models.Model):
    # EligibilityForm is primary_key, linking to Patient. No direct nullability needed here.
    patient = models.OneToOneField(Patient, primary_key=True, on_delete=models.CASCADE)
    # age = models.PositiveIntegerField()
    # birth_date = models.CharField(max_length=100)
    # weight = models.FloatField()
    # height = models.FloatField()
    # blood_type = models.CharField(max_length=20)
    # allergies = models.CharField(max_length=100)
    # medications = models.CharField(max_length=100)
    #address = models.CharField(max_length=50)
    blood_pressure = models.CharField(max_length=20)
    competetions = models.CharField(max_length=100)
    date_of_event = models.CharField(max_length=100)
    venue = models.CharField(max_length=100)
    date_of_examination = models.CharField(max_length=100)
    liscence_number = models.CharField(max_length=50)
    validity_date = models.CharField(max_length=100)
    
class MedicalCertificate(models.Model):
    # MedicalCertificate is primary_key, linking to Patient. No direct nullability needed here.
    patient = models.OneToOneField(Patient, primary_key=True, on_delete=models.CASCADE)
    college = models.CharField(max_length=100)
    year = models.CharField(max_length=50)
    age = models.PositiveIntegerField()
    height = models.FloatField()
    weight = models.FloatField()
    bp = models.CharField(max_length=20)
    p = models.CharField(max_length=20)
    t = models.CharField(max_length=20)
    rr = models.CharField(max_length=20)
    sports_played = models.CharField(max_length=255)
    physically_able = models.BooleanField(default=False)
    physically_not_able = models.BooleanField(default=False)

class PatientRequest(models.Model):
    REQUEST_STATUS = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed')
    ]
    
    request_id = models.AutoField(primary_key=True)
    # Link to Patient, make nullable initially
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, null=True, blank=True)
    request_type = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=REQUEST_STATUS, default='pending')
    date_requested = models.DateTimeField(auto_now_add=True)
    date_responded = models.DateTimeField(null=True, blank=True)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='responded_requests')
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        if self.patient:
            return f"{self.request_type} request for {self.patient.user.get_full_name() or self.patient.user.username}"
        elif self.faculty:
            return f"{self.request_type} request for {self.faculty.user.get_full_name() or self.faculty.user.username}"
        else:
            return f"{self.request_type} request for unknown user"

class FacultyRequest(models.Model):
    REQUEST_STATUS = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed')
    ]
    
    request_id = models.AutoField(primary_key=True)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    request_type = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=REQUEST_STATUS, default='pending')
    date_requested = models.DateTimeField(auto_now_add=True)
    date_responded = models.DateTimeField(null=True, blank=True)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='responded_faculty_requests')
    remarks = models.TextField(blank=True, null=True)
    is_urgent = models.BooleanField(default=False)
    priority_level = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], default='medium')

    def __str__(self):
        return f"{self.request_type} request from {self.faculty.user.get_full_name() or self.faculty.user.username}"

    class Meta:
        verbose_name = "Faculty Request"
        verbose_name_plural = "Faculty Requests"
        ordering = ['-date_requested', 'is_urgent']

class PrescriptionRecord(models.Model):
    # Link to Patient, make nullable initially
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    problem = models.CharField(max_length=50)
    treatment = models.CharField(max_length=50)
    date_prescribed = models.CharField(max_length=100)

    def __str__(self):
        return f"Prescription for {self.patient.user.get_full_name() or self.patient.user.username}"

class DentalRecords(models.Model):
    # Link to Patient, make nullable initially
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True)
    service_type = models.CharField(max_length=50)
    date_requested = models.DateTimeField()
    date_appointed = models.DateField(null=True)
    appointed = models.BooleanField(default=False)
    # def __str__(self):
    #     pass

class EmergencyHealthAssistanceRecord(models.Model):
    # Link to Patient, make nullable initially
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    reason = models.CharField(max_length=100)
    date_assisted = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.patient.user.get_full_name() or self.patient.user.username}"

class TransactionRecord(models.Model):
    # Link to Patient, make nullable initially
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True)
    transac_type = models.CharField(max_length=100)
    transac_date = models.DateTimeField()

    # def __str__(self):
    #     return f"{self.student.firstname} {self.student.lastname}"
    
class MentalHealthRecord(models.Model):
    # Link to Patient, make nullable initially
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True)
    faculty = models.OneToOneField(Faculty, on_delete=models.CASCADE, null=True, blank=True)
    is_availing_mental_health = models.BooleanField(default=False)
    
    def mental_health_path(instance, filename, field_name):
        # Use patient's user or faculty's user for path
        if instance.patient and instance.patient.user:
            user_identifier = instance.patient.user.username or instance.patient.user.id
        elif hasattr(instance, 'faculty') and instance.faculty and instance.faculty.user:
            user_identifier = instance.faculty.user.username or instance.faculty.user.id
        else:
            user_identifier = 'unknown_user'
        return os.path.join('medical', f'{user_identifier}', 'mental_health', field_name, filename)
    
    def prescription_path(instance, filename):
        return MentalHealthRecord.mental_health_path(instance, filename, 'prescriptions')
    
    def certification_path(instance, filename):
        return MentalHealthRecord.mental_health_path(instance, filename, 'certifications')
    
    prescription = models.FileField(upload_to=prescription_path, null=True, blank=True)
    certification = models.FileField(upload_to=certification_path, null=True, blank=True)
    date_submitted = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')
    prescription_remarks = models.TextField(blank=True, null=True)
    certification_remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'Mental Health Record for {self.patient.user.get_full_name() or self.patient.user.username}'
    