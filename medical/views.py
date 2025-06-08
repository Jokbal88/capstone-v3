from django.db import IntegrityError
from django.db import models  # Add this import
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.contrib import messages
from django.http import JsonResponse
from datetime import datetime
from datetime import date
from django.utils import timezone
from datetime import timedelta  
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from . models import(
    Patient,
    MedicalClearance,
    PhysicalExamination,
    RiskAssessment, 
    MedicalRequirement, 
    PatientRequest, 
    Student,
    TransactionRecord,
    MedicalHistory,
    FamilyMedicalHistory,
    ObgyneHistory,
    DentalRecords,
    EligibilityForm,
    EmergencyHealthAssistanceRecord,
    PrescriptionRecord,
    MedicalCertificate,
    MentalHealthRecord,
    FacultyRequest
)
from django.core.mail import send_mail
from django.conf import settings
import json
import calendar
import csv
from django.contrib.auth.decorators import user_passes_test, login_required
import os

from .forms import UploadFileForm
from django.template.loader import render_to_string
from django.urls import reverse
from main.models import Faculty

# Helper functions to get student/faculty by user
def get_student_by_user(user):
    """Get the Student object associated with a User, if it exists."""
    try:
        return Student.objects.get(email=user.email)
    except Student.DoesNotExist:
        return None

def get_faculty_by_user(user):
    """Get the Faculty object associated with a User, if it exists."""
    try:
        return Faculty.objects.get(user=user)
    except Faculty.DoesNotExist:
        return None

# Add this function at the top of the file
def is_admin(user):
    return user.is_superuser or user.is_staff

# Patient's basic information
def patient_basic_info(request, student_id):
    student = Student.objects.get(student_id=student_id)
    user = User.objects.get(email=student.email)
    if Patient.objects.filter(user=user).exists():
        patient = Patient.objects.get(user=user)
        return render(request, "students/basicinfo.html", {"student": student, "patient": patient})
    if request.method == "POST":
        birth_date = request.POST.get("birth_date")
        age = request.POST.get("age")
        weight = request.POST.get("weight")
        height = request.POST.get("height")
        bloodtype = request.POST.get("bloodtype")
        allergies = request.POST.get("allergies")
        medications = request.POST.get("medications")
        home_address = request.POST.get("home_address")
        city = request.POST.get("city")
        state_province = request.POST.get("state-province")
        postal_zipcode = request.POST.get("postal-zip-code")
        country = request.POST.get("country")
        nationality = request.POST.get("nationality")
        religion = request.POST.get("religion")
        civil_status = request.POST.get("civil_status")
        number_of_children = request.POST.get("number_of_children")
        academic_year = request.POST.get("academic_year")
        section = request.POST.get("section")
        parent_guardian = request.POST.get("parent_guardian")
        parent_guardian_contact_number = request.POST.get("parent_guardian_contact_number")

        Patient.objects.create(
            user = user,
            birth_date = birth_date,
            age = age,
            weight = weight,
            height = height,
            bloodtype = bloodtype,
            allergies = allergies,
            medications = medications,
            home_address = home_address,
            city = city,
            state_province = state_province,
            postal_zipcode = postal_zipcode,
            country = country,
            nationality = nationality,
            religion = religion,
            civil_status = civil_status,
            number_of_children = number_of_children,
            academic_year = academic_year,
            section = section,
            parent_guardian = parent_guardian,
            parent_guardian_contact_number = parent_guardian_contact_number
        )

        messages.success(request, "You may now do your transactions")
        return redirect("medical:request")
    return render(request, "students/basicinfo.html", {"student": student})

# view for handling clearance form submission
@user_passes_test(is_admin)
def medicalclearance_view(request, student_id):
        try:
            student = Student.objects.get(student_id=student_id)
            user = User.objects.get(email=student.email)
            patient = Patient.objects.get(user=user)
        except (Student.DoesNotExist, User.DoesNotExist, Patient.DoesNotExist):
            messages.error(request, "Student, User, or Patient record not found.")
            return redirect('medical:viewrequest') # Redirect to a safe page
        
        if request.method == "POST":
            # Handle patient basic information
            age = request.POST.get("age")
            birth_date = request.POST.get("birth-date")
            street_address = request.POST.get("street-address")
            city = request.POST.get("city")
            state_province = request.POST.get("state-province")
            postal_zip_code = request.POST.get("postal-zip-code")
            country = request.POST.get("country")

            # student = Student.objects.get(student_id=student_id)
            # patient = Patient.objects.get(student__student_id = student_id)
            
            # Handle risk assessment 
            age_above_60 = request.POST.get("age_above_60") == "True"
            cardiovascular_disease = request.POST.get("cardiovascular-disease") == "True"
            chronic_lung_disease = request.POST.get("lung-disease") == "True"
            chronic_metabolic_disease = request.POST.get("diabetes") == "True"
            chronic_renal_disease = request.POST.get("renal-disease") == "True"
            chronic_liver_disease = request.POST.get("liver-disease") == "True"
            cancer = request.POST.get("cancer") == "True"
            autoimmune_disease = request.POST.get("autoimmune") == "True"
            pregnant = request.POST.get("pregnant") == "True"
            other_conditions = request.POST.get("other_conditions")
            living_with_vulnerable = request.POST.get("living_with_vulnerable") == "True"
            pwd = request.POST.get("pwd") == "True"
            disability = request.POST.get("disability_type")
            
            # Handles medical requirements 
            vaccination_type = request.POST.get("vaccination_type")
            vaccinated_1st = request.POST.get("vaccinated_1st", "off") == "on"
            vaccinated_2nd = request.POST.get("vaccinated_2nd", "off") == "on"
            vaccinated_booster = request.POST.get("vaccinated_booster", "off") == "on"

            x_ray_remarks = request.POST.get("x-ray-remark")
            cbc_remarks = request.POST.get("cbc-remark")
            drug_test_remarks = request.POST.get("drug-test-remark")
            stool_examination_remarks = request.POST.get("stool-examination-remark")
                
            # Insert medical requirements files
            try:
                med_requirements = MedicalRequirement.objects.get(patient__student__student_id = student_id)
                med_requirements.vaccination_type = vaccination_type
                med_requirements.vaccinated_1st = vaccinated_1st
                med_requirements.vaccinated_2nd = vaccinated_2nd
                med_requirements.vaccinated_booster = vaccinated_booster
                med_requirements.x_ray_remarks = x_ray_remarks
                med_requirements.cbc_remarks = cbc_remarks
                med_requirements.drug_test_remarks = drug_test_remarks
                med_requirements.stool_examination_remarks = stool_examination_remarks
                med_requirements.pwd_card_remarks = request.POST.get("pwd-card-remark")
                med_requirements.save()
            except MedicalRequirement.DoesNotExist:
                messages.error(request, "This patient doesn't have a medical requirements")
                return render(request, "admin/patientclearance_comp.html", {"patient":patient})

            if MedicalClearance.objects.filter(patient__student__student_id = student_id).exists():
                clearance = MedicalClearance.objects.get(patient__student__student_id = student_id)
                # Get MedicalRequirement for the fetched patient
                med_requirements = MedicalRequirement.objects.get(patient=patient)

                clearance.patient.age = age
                clearance.patient.birth_date = birth_date
                clearance.patient.home_address = street_address
                clearance.patient.city = city
                clearance.patient.state_province = state_province
                clearance.patient.postal_zipcode = postal_zip_code
                clearance.patient.country = country
                

                # Update Risk Ass
                riskass = RiskAssessment.objects.get(clearance__patient__student__student_id = student_id)
                riskass.age_above_60 = age_above_60
                riskass.cardiovascular_disease = cardiovascular_disease
                riskass.chronic_lung_disease = chronic_lung_disease
                riskass.chronic_metabolic_disease = chronic_metabolic_disease
                riskass.chronic_renal_disease = chronic_renal_disease
                riskass.chronic_liver_disease = chronic_liver_disease
                riskass.cancer = cancer
                riskass.autoimmune_disease = autoimmune_disease
                riskass.pregnant = pregnant
                riskass.other_conditions = other_conditions
                riskass.living_with_vulnerable = living_with_vulnerable
                riskass.pwd = pwd
                riskass.disability = disability
                

                # Update Medical Requirements
                med_requirements_files = MedicalRequirement.objects.get(patient=patient)
                med_requirements_files.vaccination_type = vaccination_type
                med_requirements_files.vaccinated_1st = vaccinated_1st
                med_requirements_files.vaccinated_2nd = vaccinated_2nd
                med_requirements_files.vaccinated_booster = vaccinated_booster
                med_requirements_files.x_ray_remarks = x_ray_remarks
                med_requirements_files.cbc_remarks = cbc_remarks
                med_requirements_files.drug_test_remarks = drug_test_remarks
                med_requirements_files.stool_examination_remarks = stool_examination_remarks
                med_requirements_files.pwd_card_remarks = request.POST.get("pwd-card-remark")
                
                # Save All
                clearance.save()
                riskass.save()
                med_requirements_files.save()
                messages.success(request, "Record Updated")
                # return render(request, "admin/patientclearance_comp.html", {"patient": patient, "clearance":clearance, "med_requirements": med_requirements})
            
            # Create the clearance object
            # patient = Student.objects.get(student_id = student_id)
            clearance = MedicalClearance.objects.create(patient = patient)

            # The risk assessment
            rsk = RiskAssessment.objects.create(
                    clearance = clearance, 
                    age_above_60 = age_above_60, 
                    cardiovascular_disease = cardiovascular_disease,
                    chronic_lung_disease = chronic_lung_disease, 
                    chronic_metabolic_disease = chronic_metabolic_disease,
                    chronic_renal_disease = chronic_renal_disease, 
                    chronic_liver_disease = chronic_liver_disease,
                    cancer = cancer, 
                    autoimmune_disease = autoimmune_disease, 
                    pregnant = pregnant, 
                    other_conditions = other_conditions, 
                    living_with_vulnerable = living_with_vulnerable,
                    pwd = pwd
                )
            # Handle if pwd
            if pwd:
                rsk.disability = disability
                rsk.save()

            # Record requests
            # patient_request = PatientRequest.objects.get(patient__student__student_id = student_id, request_type = "Medical Clearance for OJT/Practicum")
        
            # patient_request.save()

            messages.success(request, "Medical Clearance created successfully.")
            # return render(request, "admin/patientclearance_comp.html", {"patient": patient, "clearance":clearance, "med_requirements": med_requirements})

        if MedicalClearance.objects.filter(patient=patient).exists():
            clearance = MedicalClearance.objects.get(patient=patient)
            # Get MedicalRequirement for the fetched patient
            med_requirements = MedicalRequirement.objects.get(patient=patient)
            return render(request, "admin/patientclearance_comp.html", {"patient": patient, "clearance": clearance, "med_requirements": med_requirements})
        # Access student's first name through the patient's user and linked student object
        student_first_name = patient.user.student.firstname if patient.user and hasattr(patient.user, 'student') and patient.user.student else 'N/A'
        messages.info(request, f"Fill out the necessary information to complete {student_first_name.title()}'s Medical Clearance.")
        return render(request, "admin/patientclearance_comp.html", {"patient":patient})

# Views for handling eligibilty form creation
@user_passes_test(is_admin)
def eligibilty_form(request, student_id):
        student = Student.objects.get(student_id=student_id)
        user = User.objects.get(email=student.email)
        patient = Patient.objects.get(user=user)
        # Get data inputted from eligibility form
        if request.method == "POST":
            age = request.POST.get("age")
            birth_date = request.POST.get("birth-date")
            weight = request.POST.get("weight")
            height = request.POST.get("height")
            blood_type = request.POST.get("blood-type")
            allergies = request.POST.get("allergies")
            medications = request.POST.get("medication")
            address = request.POST.get("address")
            competetions = request.POST.get("competition")
            date_event = request.POST.get("date-event")
            venue = request.POST.get("place-event")
            blood_pressure = request.POST.get("blood-pressure")
            date_of_examination = request.POST.get("date-exam")
            license_number = request.POST.get("liscence-number")
            validity_date = request.POST.get("validity-date")

            # Check if EligibilityForm exists for the patient
            if EligibilityForm.objects.filter(patient=patient).exists():
                patient_eligibilty_form = EligibilityForm.objects.get(patient=patient)

                # Update the existing EligibilityForm and patient basic info
                patient_eligibilty_form.patient.age = age
                patient_eligibilty_form.patient.birth_date = birth_date
                patient_eligibilty_form.patient.weight = weight
                patient_eligibilty_form.patient.height = height
                patient_eligibilty_form.patient.bloodtype = blood_type
                patient_eligibilty_form.patient.allergies = allergies
                patient_eligibilty_form.patient.medications = medications
                patient_eligibilty_form.patient.home_address = address
                patient_eligibilty_form.blood_pressure = blood_pressure
                patient_eligibilty_form.date_of_event = date_event
                # competetions field assignment was incorrect, assuming it's a single value
                patient_eligibilty_form.competetions = competetions
                patient_eligibilty_form.venue = venue
                patient_eligibilty_form.date_of_examination = date_of_examination
                patient_eligibilty_form.liscence_number = license_number
                patient_eligibilty_form.validity_date = validity_date

                patient_eligibilty_form.patient.save()
                patient_eligibilty_form.save()

                messages.success(request, "Eligibility Form record updated.")
                return render(request, "admin/eligibilityformcomp.html", {"patient": patient, "eligibility_form": patient_eligibilty_form})

            else:
                # Create the EligibilityForm object if it does not exists
                patient_eligibilty_form = EligibilityForm.objects.create(
                    patient = patient,
                    blood_pressure = blood_pressure,
                    competetions = competetions,
                    date_of_event = date_event,
                    venue = venue,
                    date_of_examination = date_of_examination,
                    liscence_number = license_number,
                    validity_date = validity_date
                )
                # Also update basic patient info when creating the eligibility form
                patient.age = age
                patient.birth_date = birth_date
                patient.weight = weight
                patient.height = height
                patient.bloodtype = blood_type
                patient.allergies = allergies
                patient.medications = medications
                patient.home_address = address
                patient.save()

                # patient_request = PatientRequest.objects.get(patient__student__student_id = student_id, request_type = "Eligibility Form")
                # student_request.date_approved = datetime.now()
                # student_request.save()

                messages.success(request, "Eligibility Form successfully created.")
                return render(request, "admin/eligibilityformcomp.html", {"patient": patient, "eligibility_form": patient_eligibilty_form})      

        # For GET request or if POST doesn't have necessary data, check if EligibilityForm exists
        if EligibilityForm.objects.filter(patient=patient).exists():
            patient_eligibilty_form = EligibilityForm.objects.get(patient=patient)
            return render(request, "admin/eligibilityformcomp.html", {"patient": patient, "eligibility_form": patient_eligibilty_form})

        # Access student's first name through the patient's user object and linked student object
        student_first_name = patient.user.student.firstname if patient.user and hasattr(patient.user, 'student') and patient.user.student else 'N/A'
        messages.info(request, f"Fill out the necessary information to complete {student_first_name.title()}'s Eligibility Form.")
        return render(request, "admin/eligibilityformcomp.html", {"patient": patient})
    
# List of student for patient profile
@user_passes_test(is_admin)
def patient_profile(request):
        # Get all students and faculty, ordered by name
        all_students = Student.objects.all().order_by('lastname', 'firstname')
        all_faculty = Faculty.objects.all().select_related('user').order_by('user__last_name', 'user__first_name')

        students_list = []
        for student in all_students:
            try:
                # Get user by email from Student model
                user = User.objects.get(email=student.email)
                # Get patient record if it exists
                patient = Patient.objects.filter(user=user).first()
                students_list.append({
                    'student': student,
                    'patient': patient
                })
            except User.DoesNotExist:
                # Handle case where student doesn't have a user account
                students_list.append({
                    'student': student,
                    'patient': None
                })

        faculty_list = []
        for faculty in all_faculty:
            try:
                # Faculty model has a direct ForeignKey to User
                user = faculty.user
                # Get patient record if it exists
                patient = Patient.objects.filter(user=user).first()
                faculty_list.append({
                    'faculty': faculty,
                    'patient': patient
                })
            except AttributeError:
                # Handle case where faculty doesn't have a user account
                faculty_list.append({
                    'faculty': faculty,
                    'patient': None
                })

        if request.method == "POST":
            search_id = request.POST.get("search_id")
            filtered_students = []
            filtered_faculty = []

            if search_id:
                # Try to find a student first
                try:
                    student = Student.objects.get(student_id=search_id)
                    user = User.objects.get(email=student.email)
                    patient = Patient.objects.filter(user=user).first()
                    filtered_students.append({
                        'student': student,
                        'patient': patient
                    })
                    messages.info(request, f"Found student with ID: {search_id}")
                except (Student.DoesNotExist, User.DoesNotExist):
                    # If not found as a student, try finding as faculty
                    try:
                        faculty = Faculty.objects.get(faculty_id=search_id)
                        user = faculty.user
                        patient = Patient.objects.filter(user=user).first()
                        filtered_faculty.append({
                            'faculty': faculty,
                            'patient': patient
                        })
                        messages.info(request, f"Found faculty with ID: {search_id}")
                    except (Faculty.DoesNotExist, AttributeError):
                        messages.warning(request, f"No student or faculty found with ID: {search_id}")
                # If a search ID was provided, only show the filtered results
                students_list = filtered_students
                faculty_list = filtered_faculty
            else:
                messages.info(request, "Displaying all registered patients.")

        return render(request, "admin/patientprofile.html", {
            "students": students_list,
            "faculty": faculty_list
        })

# View students request, eg. Medical Clearance for OJT/Practicum, Eligibility Form and Medical Certificate
@user_passes_test(is_admin)
def view_request(request):
    # Fetch all patient requests and filter by status
    pending_patient_requests = PatientRequest.objects.select_related('patient__user').filter(
        status='pending'
    )
    accepted_patient_requests = PatientRequest.objects.select_related('patient__user').filter(
        status='accepted'
    )
    completed_patient_requests = PatientRequest.objects.select_related('patient__user').filter(
        status='completed'
    )

    # Fetch all faculty requests and filter by status
    pending_faculty_requests = FacultyRequest.objects.select_related('faculty__user').filter(status='pending')
    accepted_faculty_requests = FacultyRequest.objects.select_related('faculty__user').filter(status='accepted')
    completed_faculty_requests = FacultyRequest.objects.select_related('faculty__user').filter(status='completed')

    # Ensure unique requests
    pending_patient_requests = pending_patient_requests.distinct()
    accepted_patient_requests = accepted_patient_requests.distinct()
    completed_patient_requests = completed_patient_requests.distinct()
    pending_faculty_requests = pending_faculty_requests.distinct()
    accepted_faculty_requests = accepted_faculty_requests.distinct()
    completed_faculty_requests = completed_faculty_requests.distinct()
    
    # Attach student/faculty ID and names to each request object for easier access in template
    from main.models import Student, Faculty

    for request_obj in pending_patient_requests:
        if request_obj.patient and request_obj.patient.user:
            try:
                student = Student.objects.get(email=request_obj.patient.user.email)
                request_obj.student_id = student.student_id
                request_obj.student_first_name = student.firstname
                request_obj.student_last_name = student.lastname
            except Student.DoesNotExist:
                request_obj.student_id = "N/A"
                request_obj.student_first_name = "N/A"
                request_obj.student_last_name = "N/A"

    for request_obj in accepted_patient_requests:
         if request_obj.patient and request_obj.patient.user:
            try:
                student = Student.objects.get(email=request_obj.patient.user.email)
                request_obj.student_id = student.student_id
                request_obj.student_first_name = student.firstname
                request_obj.student_last_name = student.lastname
            except Student.DoesNotExist:
                request_obj.student_id = "N/A"
                request_obj.student_first_name = "N/A"
                request_obj.student_last_name = "N/A"

    for request_obj in completed_patient_requests:
         if request_obj.patient and request_obj.patient.user:
            try:
                student = Student.objects.get(email=request_obj.patient.user.email)
                request_obj.student_id = student.student_id
                request_obj.student_first_name = student.firstname
                request_obj.student_last_name = student.lastname
            except Student.DoesNotExist:
                request_obj.student_id = "N/A"
                request_obj.student_first_name = "N/A"
                request_obj.student_last_name = "N/A"

    for request_obj in pending_faculty_requests:
        if request_obj.faculty:
            request_obj.faculty_id = request_obj.faculty.faculty_id
        else:
            request_obj.faculty_id = "N/A"
            
    for request_obj in accepted_faculty_requests:
        if request_obj.faculty:
            request_obj.faculty_id = request_obj.faculty.faculty_id
        else:
            request_obj.faculty_id = "N/A"

    for request_obj in completed_faculty_requests:
        if request_obj.faculty:
            request_obj.faculty_id = request_obj.faculty.faculty_id
        else:
            request_obj.faculty_id = "N/A"

    
    if request.method == "POST":
        request_id = request.POST.get("request_id")
        request_type_model = request.POST.get("request_type_model") # 'PatientRequest' or 'FacultyRequest'
        action = request.POST.get("action")
        remarks = request.POST.get("remarks") # Get remarks from the form

        try:
            if request_type_model == 'PatientRequest':
                request_obj = get_object_or_404(PatientRequest, request_id=request_id)
            elif request_type_model == 'FacultyRequest':
                request_obj = get_object_or_404(FacultyRequest, request_id=request_id)
            else:
                messages.error(request, "Invalid request type.")
                return redirect('medical:viewrequest')

            if action == "accept":
                request_obj.status = 'accepted'
                request_obj.date_responded = timezone.now()
                request_obj.responded_by = request.user
                request_obj.remarks = remarks
                request_obj.save()
                messages.success(request, "Request marked as accepted")

                # Send acceptance email
                user = None
                if request_type_model == 'PatientRequest' and request_obj.patient and request_obj.patient.user:
                    user = request_obj.patient.user
                elif request_type_model == 'FacultyRequest' and request_obj.faculty and request_obj.faculty.user:
                    user = request_obj.faculty.user
                
                if user and user.email:
                    approval_email_subject = f'{request_obj.request_type} Request Accepted'
                    approval_email_body = f"""
                        <html>
                        <head>
                            <style>
                                body {{
                                    font-family: Arial, sans-serif;
                                    line-height: 1.6;
                                    color: #333;
                                    margin: 0;
                                    padding: 20px;
                                    background-color: #f4f4f4;
                                    text-align: center;
                                }}
                                .container {{
                                    max-width: 600px;
                                    margin: 0 auto;
                                    background-color: #fff;
                                    padding: 30px;
                                    border-radius: 8px;
                                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                                    text-align: left;
                                }}
                                .title {{
                                    text-align: center;
                                    font-size: 24px;
                                    color: #0056b3;
                                    margin-bottom: 20px;
                                    padding-bottom: 15px;
                                    border-bottom: 1px solid #eee;
                                }}
                                 p {{
                                    margin-bottom: 15px;
                                }}
                                 .footer {{
                                    margin-top: 30px;
                                    padding-top: 20px;
                                    font-size: 12px;
                                    color: #999;
                                    text-align: center;
                                    border-top: 1px solid #eee;
                                }}
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <div class="title">REQUEST ACCEPTED</div>
                                <p>Dear <strong>{user.get_full_name() or user.username}</strong>,</p>
                                <p>Your request for <strong>'{request_obj.request_type}'</strong> has been <strong style='color:green;'>ACCEPTED</strong>.</p>
                                <p>Remarks from the clinic: {remarks or 'None provided'}</p>
                                <p>Please log in to your account for more details or further instructions.</p>
                                <p>Best Regards,</p>
                                <p><strong>CTU - Argao Campus Kahimsug Clinic</strong></p>
                            </div>
                             <div class="footer">
                                <p>This is an automated message, please do not reply to this email.</p>
                                <p>&copy; 2024 HealthHub Connect. All rights reserved.</p>
                            </div>
                        </body>
                        </html>
                    """

                    send_mail(
                        approval_email_subject,
                        '',
                        settings.EMAIL_HOST_USER,
                        [user.email],
                        html_message=approval_email_body,
                        fail_silently=False,
                    )

            elif action == "reject":
                request_obj.status = 'rejected'
                request_obj.date_responded = timezone.now()
                request_obj.responded_by = request.user
                request_obj.remarks = remarks
                request_obj.save()
                messages.error(request, "Request marked as rejected")

                # Send rejection email
                user = None
                if request_type_model == 'PatientRequest' and request_obj.patient and request_obj.patient.user:
                    user = request_obj.patient.user
                elif request_type_model == 'FacultyRequest' and request_obj.faculty and request_obj.faculty.user:
                    user = request_obj.faculty.user
                
                if user and user.email:
                    rejection_email_subject = f'{request_obj.request_type} Request Rejected'
                    rejection_email_body = f"""
                        <html>
                        <head>
                            <style>
                                body {{
                                    font-family: Arial, sans-serif;
                                    line-height: 1.6;
                                    color: #333;
                                    margin: 0;
                                    padding: 20px;
                                    background-color: #f4f4f4;
                                    text-align: center;
                                }}
                                .container {{
                                    max-width: 600px;
                                    margin: 0 auto;
                                    background-color: #fff;
                                    padding: 30px;
                                    border-radius: 8px;
                                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                                    text-align: left;
                                }}
                                .title {{
                                    text-align: center;
                                    font-size: 24px;
                                    color: #d9534f;
                                    margin-bottom: 20px;
                                    padding-bottom: 15px;
                                    border-bottom: 1px solid #eee;
                                }}
                                p {{
                                    margin-bottom: 15px;
                                }}
                                .footer {{
                                    margin-top: 30px;
                                    padding-top: 20px;
                                    font-size: 12px;
                                    color: #999;
                                    text-align: center;
                                    border-top: 1px solid #eee;
                                }}
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <div class="title">REQUEST REJECTED</div>
                                <p>Dear <strong>{user.get_full_name() or user.username}</strong>,</p>
                                <p>We regret to inform you that your request for <strong>'{request_obj.request_type}'</strong> has been <strong style='color:red;'>REJECTED</strong>.</p>
                                <p>Remarks from the clinic: {remarks or 'None provided'}</p>
                                <p>Please review the requirements and resubmit your request if necessary.</p>
                                <p>Best Regards,</p>
                                <p><strong>CTU - Argao Campus Kahimsug Clinic</strong></p>
                            </div>
                            <div class="footer">
                                <p>This is an automated message, please do not reply to this email.</p>
                                <p>&copy; 2024 HealthHub Connect. All rights reserved.</p>
                            </div>
                        </body>
                        </html>
                    """

                    send_mail(
                        rejection_email_subject,
                        '',
                        settings.EMAIL_HOST_USER,
                        [user.email],
                        html_message=rejection_email_body,
                        fail_silently=False,
                    )

            elif action == "complete":
                request_obj.status = 'completed'
                request_obj.date_responded = timezone.now()
                request_obj.responded_by = request.user
                request_obj.remarks = remarks
                request_obj.save()
                messages.success(request, "Request marked as completed")

                # Create a transaction record
                if request_type_model == 'PatientRequest' and request_obj.patient:
                    TransactionRecord.objects.create(
                        patient=request_obj.patient,
                        transac_type="Medical Document Request",  # Changed to match dropdown
                        transac_date=timezone.now()
                    )
                elif request_type_model == 'FacultyRequest' and request_obj.faculty:
                    print(f"Transaction completed for faculty request ID {request_id} (Type: {request_obj.request_type})")

        except (PatientRequest.DoesNotExist, FacultyRequest.DoesNotExist) as e:
            messages.error(request, f"Request not found: {e}")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")

        return redirect('medical:viewrequest')

    # Pass filtered requests to the template
    context = {
        "pending_patient_requests": pending_patient_requests,
        "accepted_patient_requests": accepted_patient_requests,
        "completed_patient_requests": completed_patient_requests,
        "pending_faculty_requests": pending_faculty_requests,
        "accepted_faculty_requests": accepted_faculty_requests,
        "completed_faculty_requests": completed_faculty_requests,
    }
    
    return render(request, "admin/viewrequest.html", context)

# Views for creating Physical Examintaion Reports
@user_passes_test(is_admin)
def physical_examination(request, id):
        student = None
        faculty = None
        user = None
        patient = None

        try:
            # Try to get a Student first
            student = Student.objects.filter(student_id=id).first()
            if student:
                user = User.objects.get(email=student.email)
                patient = Patient.objects.get(user=user)
            else:
                # If not a student, try to get a Faculty
                faculty = Faculty.objects.filter(faculty_id=id).first()
                if faculty:
                    user = faculty.user
                    patient = Patient.objects.filter(user=user).first() # Faculty may or may not have a patient record

            # If neither student nor faculty was found with the provided ID
            if not student and not faculty:
                messages.error(request, f"No student or faculty found with ID: {id}")
                return redirect("medical:patient_profile")

            # If a student or faculty was found, but no associated user or patient record exists
            if (student and not (user and patient)) or (faculty and not user):
                 if student:
                     messages.error(request, f"User or Patient record not found for student with ID: {id}")
                 elif faculty:
                     messages.error(request, f"User record not found for faculty with ID: {id}")
                 return redirect("medical:patient_profile")

        except User.DoesNotExist:
            # This should be caught by the check above, but as a fallback:
            messages.error(request, f"User account not found for the ID: {id}")
            return redirect("medical:patient_profile")
        except Patient.DoesNotExist:
             # This should be caught by the check above, but as a fallback:
            messages.error(request, f"Patient record not found for the ID: {id}")
            return redirect("medical:patient_profile")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {str(e)}")
            return redirect("medical:patient_profile")

        if request.method == "POST":
            # Get patient basic information
            birth_date = request.POST.get("birth_date")
            date_of_physical_examination = request.POST.get("date")
            address = request.POST.get("home_address")
            age = request.POST.get("age")
            nationality = request.POST.get("nationality")
            civil_status = request.POST.get("civil_status")
            number_of_children = request.POST.get("number_of_children", 0)
            academic_year = request.POST.get("academic_year")
            section = request.POST.get("academic_year")
            parent_guardian = request.POST.get("parent_guardian")
            parent_contact = request.POST.get("parent_guardian_contact_number")
            
            # Get patient medical history
            tuberculosis = request.POST.get("tuberculosis") == "on"
            peptic_ulcer = request.POST.get("peptic-ulcer") == "on"
            venereal = request.POST.get("venereal-disease") == "on"
            hypertension = request.POST.get("hypertension") == "on"
            kidney_disease = request.POST.get("kidney-disease") == "on"
            allergic_reaction = request.POST.get("allergic-reaction") == "on"
            heart_disease = request.POST.get("heart-diseases") == "on"
            asthma = request.POST.get("asthma") == "on"
            nervous_breakdown = request.POST.get("nervous-breakdown") == "on"
            hernia = request.POST.get("hernia") == "on"
            insomnia = request.POST.get("insomnia") == "on"
            jaundice = request.POST.get("jaundice") == "on"
            epilepsy = request.POST.get("epilepsy") == "on"
            malaria = request.POST.get("malaria") == "on"
            others = request.POST.get("others")
            no_history = request.POST.get("none") == "on"
            hospital_admission = request.POST.get("operations")
            medications = request.POST.get("medications")

            # Get patient's family medical history
            hypertension_family = request.POST.get("hypertension-family") == "on"
            tuberculosis_family = request.POST.get("tuberculosis-family") == "on"
            asthma_family = request.POST.get("asthma-family") == "on"
            diabetes = request.POST.get("diabetes") == "on"
            cancer = request.POST.get("cancer") == "on"
            bleeding_disorder = request.POST.get("bleeding-disorder") == "on"
            epilepsy_family = request.POST.get("epilepsy-family") == "on"
            mental_disorders = request.POST.get("mental-disorders") == "on"
            family_others = request.POST.get("family-others")
            family_no_history = request.POST.get("no_history") == "on"

            # Get OB-GYNE history
            menarche = request.POST.get("menarche")
            lmp = request.POST.get("lmp")
            gravida = request.POST.get("gravida")
            para = request.POST.get("para")
            menopause = request.POST.get("menopause")
            pap_smear = request.POST.get("pap_swear")
            additional_history = request.POST.get("additional-history")

            # Check if object already exists
            if PhysicalExamination.objects.filter(patient=patient).exists():
                examination = PhysicalExamination.objects.get(patient=patient)

                # Update Physical Examination
                examination.patient.birth_date = birth_date
                examination.patient.home_address = address
                examination.patient.age = age
                examination.patient.nationality = nationality
                examination.patient.civil_status = civil_status
                examination.patient.number_of_children = number_of_children
                examination.patient.academic_year = academic_year
                examination.patient.section = section
                examination.date_of_physical_examination = date_of_physical_examination
                examination.patient.parent_guardian = parent_guardian
                examination.patient.parent_guardian_contact_number = parent_contact
                # Save
                examination.patient.save()
                examination.save()

                # Update or create Medical History
                medical_history, created = MedicalHistory.objects.update_or_create(
                    examination=examination,
                    defaults={
                        'tuberculosis': tuberculosis,
                        'hypertension': hypertension,
                        'heart_disease': heart_disease,
                        'hernia': hernia,
                        'epilepsy': epilepsy,
                        'peptic_ulcer': peptic_ulcer,
                        'kidney_disease': kidney_disease,
                        'asthma': asthma,
                        'insomnia': insomnia,
                        'malaria': malaria,
                        'venereal_disease': venereal,
                        'allergic_reaction': allergic_reaction,
                        'nervous_breakdown': nervous_breakdown,
                        'jaundice': jaundice,
                        'others': others,
                        'no_history': no_history,
                        'hospital_admission': hospital_admission,
                        'medications': medications
                    }
                )

                # Update or create Family History
                family_history, created = FamilyMedicalHistory.objects.update_or_create(
                    examination=examination,
                    defaults={
                        'hypertension': hypertension_family,
                        'asthma': asthma_family,
                        'cancer': cancer,
                        'tuberculosis': tuberculosis_family,
                        'diabetes': diabetes,
                        'bleeding_disorder': bleeding_disorder,
                        'epilepsy': epilepsy_family,
                        'mental_disorder': mental_disorders,
                        'no_history': family_no_history,
                        'other_medical_history': family_others
                    }
                )

                # Update or create Obgyne History
                obgyne, created = ObgyneHistory.objects.update_or_create(
                    examination=examination,
                    defaults={
                        'menarche': menarche,
                        'lmp': lmp,
                        'pap_smear': pap_smear,
                        'gravida': gravida,
                        'para': para,
                        'menopause': menopause,
                        'additional_history': additional_history
                    }
                )

                messages.success(request, "Record Updated")
                record_transaction(patient, "Physical Examination")
                return render(request, "admin/physicalexamcomp.html", {"examination": examination, "patient": patient, "student": student, "faculty": faculty})
        
            # Create the physical examination object if it does not exists
            examination = PhysicalExamination.objects.create(
                patient=patient,
                date_of_physical_examination=date_of_physical_examination
            )

            # Update patient information
            patient.birth_date = birth_date
            patient.home_address = address
            patient.age = age
            patient.nationality = nationality
            patient.civil_status = civil_status
            patient.number_of_children = number_of_children
            patient.academic_year = academic_year
            patient.section = section
            patient.parent_guardian = parent_guardian
            patient.parent_guardian_contact_number = parent_contact
            patient.save()

            # Insert data into the medical history of the patients model
            MedicalHistory.objects.create(
                examination=examination,
                tuberculosis=tuberculosis,
                hypertension=hypertension,
                heart_disease=heart_disease,
                hernia=hernia,
                epilepsy=epilepsy,
                peptic_ulcer=peptic_ulcer,
                kidney_disease=kidney_disease,
                asthma=asthma,
                insomnia=insomnia,
                malaria=malaria,
                venereal_disease=venereal,
                allergic_reaction=allergic_reaction,
                nervous_breakdown=nervous_breakdown,
                jaundice=jaundice,
                others=others,
                no_history=no_history,
                hospital_admission=hospital_admission,
                medications=medications
            )

            # Insert data into the family medical history of the patients model
            FamilyMedicalHistory.objects.create(
                examination=examination,
                hypertension=hypertension_family,
                asthma=asthma_family,
                cancer=cancer,
                tuberculosis=tuberculosis_family,
                diabetes=diabetes,
                bleeding_disorder=bleeding_disorder,
                epilepsy=epilepsy_family,
                mental_disorder=mental_disorders,
                no_history=family_no_history,
                other_medical_history=family_others
            )

            # Insert data into the OB-GYNE history of the patients model
            ObgyneHistory.objects.create(
                examination=examination,
                menarche=menarche,
                lmp=lmp,
                pap_smear=pap_smear,
                gravida=gravida,
                para=para,
                menopause=menopause,
                additional_history=additional_history
            )

            messages.success(request, "Record Created")
            record_transaction(patient, "Physical Examination")
            return render(request, "admin/physicalexamcomp.html", {"examination": examination, "patient": patient, "student": student, "faculty": faculty})

        # GET request - show the form
        context = {
            "patient": patient,
            "student": student,
            "faculty": faculty, # Pass faculty object to the template
        }
        # Try to fetch existing examination and related histories
        try:
            examination = PhysicalExamination.objects.get(patient=patient)
            context['examination'] = examination
            context['medicalhistory'] = MedicalHistory.objects.filter(examination=examination).first()
            context['familymedicalhistory'] = FamilyMedicalHistory.objects.filter(examination=examination).first()
            context['obgynehistory'] = ObgyneHistory.objects.filter(examination=examination).first()
        except PhysicalExamination.DoesNotExist:
            pass # No existing examination, context will not have these objects

        return render(request, "admin/physicalexamcomp.html", context)

# Record prescriptions
@user_passes_test(is_admin)
def prescription(request):
        if request.method == "POST":
            id_number = request.POST.get("student_id") # Use id_number to be consistent with other views and handle both student and faculty IDs
            name = request.POST.get("name")
            problem = request.POST.get("problem")
            treatment = request.POST.get("treatment") # Added missing treatment retrieval
            str_date_prescribed = request.POST.get("date_prescribed")
            date_prescribed = datetime.strptime(str_date_prescribed, "%Y-%m-%d")

            user = None
            patient = None
            user_name = ""

            try:
                # Try to find a Student first by student_id
                student = Student.objects.filter(student_id=id_number).first()
                if student:
                    user = User.objects.get(email=student.email)
                    user_name = f"{student.firstname} {student.lastname}".title()
                else:
                    # If not a student, try to find a Faculty by faculty_id
                    faculty = Faculty.objects.filter(faculty_id=id_number).first()
                    if faculty and faculty.user:
                        user = faculty.user
                        user_name = faculty.user.get_full_name() or faculty.user.username

                # If a user is found, get or create the patient profile
                if user:
                     patient, created = Patient.objects.get_or_create(user=user)
                     if created:
                         messages.info(request, f"Patient profile created for {user_name} (ID: {id_number}).")

                # If neither student nor faculty was found, or no user associated with faculty
                if not user or not patient:
                    messages.error(request, f"No student or faculty found with ID: {id_number} or no associated user/patient profile.")
                    return render(request, "admin/prescription.html", { 'student_id': id_number, 'name': name, 'problem': problem, 'treatment': treatment, 'date_prescribed': str_date_prescribed})

                # Validate inputted name against the retrieved user's name (case-insensitive)
                if name.lower() != user_name.lower():
                    messages.error(request, "The entered name does not match the name associated with the inputted ID Number.")
                    # Return existing values to the form for correction
                    return render(request, "admin/prescription.html", {
                        'student_id': id_number, # Use student_id to match the form field name
                        'name': name,
                        'problem': problem,
                        'treatment': treatment,
                        'date_prescribed': str_date_prescribed # Pass back as string
                    })

                # Create prescription record
                PrescriptionRecord.objects.create(
                    patient=patient,
                    name=user_name, # Use the verified name from the database
                    problem=problem,
                    treatment=treatment,
                    date_prescribed=date_prescribed
                )

                messages.success(request, "Record Saved")
                record_transaction(patient, "Prescription Issuance")
                # Redirect to the same page to clear the form after successful submission
                return redirect('medical:prescription')

            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
                # Return existing values to the form in case of other errors
                return render(request, "admin/prescription.html", { 'student_id': id_number, 'name': name, 'problem': problem, 'treatment': treatment, 'date_prescribed': str_date_prescribed})

        else:
            return render(request, "admin/prescription.html", {})

@user_passes_test(is_admin)
def get_user_name_by_id(request):
    if request.method == "POST":
        data = json.loads(request.body)
        id_number = data.get("student_id") # The input name from the form is 'student_id'

        try:
            # Try to find a Student first
            student = Student.objects.filter(student_id=id_number).first()
            if student:
                user_name = f"{student.firstname} {student.lastname}".title()
                return JsonResponse({"user_name": user_name})
            else:
                # If not a student, try to find a Faculty
                faculty = Faculty.objects.filter(faculty_id=id_number).first()
                if faculty and faculty.user:
                    user_name = faculty.user.get_full_name() or faculty.user.username
                    return JsonResponse({"user_name": user_name})     
                else:
                    return JsonResponse({"error": "User not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=405)

#check if student matched
# def check_student_match(request):
#     if request.method == "GET":
#         student_id = request.GET.get("student_id")
#         name = request.GET.get("name")

#         try:
#             student = Student.objects.get(student_id=student_id)
#             student_name = f"{student.firstname} {student.lastname}"

#             # Check if the provided name matches the student name associated with the student ID
#             if name.lower() == student_name.lower():
#                 return JsonResponse({'success': True})
#             else:
#                 return JsonResponse({'success': False, 'message': 'Student name does not match the provided name'})
#         except Student.DoesNotExist:
#             return JsonResponse({'success': False, 'message': 'Student with the provided ID does not exist'})   

# Record Emergency Health Assistance
@user_passes_test(is_admin)
def emergency_asst(request):
        if request.method == "POST":
            # Get the ID number from the form
            id_number = request.POST.get("student_id") # The input name is 'student_id' but it can be faculty ID
            name = request.POST.get("name")
            reason = request.POST.get("problem")
            str_date_assisted = request.POST.get("date_assisted")

            # Validate date format and convert to datetime object
            try:
                date_assisted = datetime.strptime(str_date_assisted, "%Y-%m-%d").date() # Store as date
            except ValueError:
                messages.error(request, "Invalid date format.")
                return render(request, "admin/emergency_asst.html", {})

            user = None
            patient = None
            user_name = ""

            try:
                # Try to find a Student first
                student = Student.objects.filter(student_id=id_number).first()
                if student:
                    user = User.objects.get(email=student.email)
                    user_name = f"{student.firstname} {student.lastname}"
                    # Get or create patient for student
                    patient, created = Patient.objects.get_or_create(user=user)
                    if created:
                        messages.info(request, f"Patient profile created for student {id_number}.")
                else:
                    # If not a student, try to find a Faculty
                    faculty = Faculty.objects.filter(faculty_id=id_number).first()
                    if faculty:
                        user = faculty.user
                        user_name = faculty.user.get_full_name() or faculty.user.username
                        # Get or create patient for faculty
                        patient, created = Patient.objects.get_or_create(user=user)
                        if created:
                             messages.info(request, f"Patient profile created for faculty {id_number}.")

                # If neither student nor faculty was found
                if not user or not patient:
                    messages.error(request, f"No student or faculty found with ID: {id_number} or could not create patient profile.")
                    return render(request, "admin/emergency_asst.html", {})

                # Validate inputted name against the retrieved user's name (case-insensitive)
                if name.lower() != user_name.lower():
                    messages.error(request, "The entered name does not match the name associated with the inputted ID Number.")
                    # Return existing values to the form for correction
                    return render(request, "admin/emergency_asst.html", {
                        'id_number': id_number,
                        'name': name,
                        'reason': reason,
                        'date_assisted': str_date_assisted # Pass back as string
                    })

                # Create EmergencyHealthAssistanceRecord
                EmergencyHealthAssistanceRecord.objects.create(
                    name=user_name, # Use the verified name from the database
                    patient=patient,
                    reason=reason,
                    date_assisted=date_assisted
                )
                messages.success(request, "Record Saved")

                # Record transaction
                record_transaction(patient, "Emergency Health Assistance")

                # Redirect after successful save and transaction recording
                return redirect('medical:emergency_asst')

            except User.DoesNotExist:
                 messages.error(request, f"User account not found for ID: {id_number}.")
                 return render(request, "admin/emergency_asst.html", {})
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
                return render(request, "admin/emergency_asst.html", {})
        
        # For GET requests, render the empty form
        return render(request, "admin/emergency_asst.html", {})

# Helper function to record transactions
def record_transaction(patient, transac_type):
    TransactionRecord.objects.create(
        patient = patient, 
        transac_type = transac_type, 
        transac_date = timezone.now()
    )

# Record students request eg. Medical Clearance for OJT/Practicum, Eligibility Form and Medical Certificate
def submit_request(request):
    from main.models import Faculty
    if request.method == "POST":
        request_type = request.POST.get("request_type")
        
        # Determine if the logged-in user is a student or faculty
        student_user = get_student_by_user(request.user)
        faculty_user = get_faculty_by_user(request.user)

        if student_user:
            # Logged-in user is a student
            student = student_user
            id_number = student.student_id
            # Check if patient exists for student
            try:
                user = request.user
                patient = Patient.objects.get(user=user)
            except Patient.DoesNotExist:
                messages.info(request, "Fill out your medical profile first before doing any transactions")
                return redirect('medical:patient_basicinfo', student.student_id)

            if PatientRequest.objects.filter(patient=patient, request_type=request_type).exists():
                messages.error(request, "You have already submitted this type of request")
                return render(request, "students/requestform.html", {"student": student, "faculty": None, "id_number": id_number})
            
            # Create student request
            request_obj = PatientRequest.objects.create(
                patient=patient,
                request_type=request_type,
                date_requested=timezone.now()
            )
            # Set name and email for confirmation email
            user_name = f"{student.firstname} {student.lastname}"
            user_email = student.email

        elif faculty_user:
            # Logged-in user is a faculty
            faculty = faculty_user
            id_number = faculty.faculty_id

            if FacultyRequest.objects.filter(faculty=faculty, request_type=request_type).exists():
                messages.error(request, "You have already submitted this type of request")
                return render(request, "students/requestform.html", {"student": None, "faculty": faculty, "id_number": id_number})
            
            # Create faculty request
            request_obj = FacultyRequest.objects.create(
                faculty=faculty,
                request_type=request_type,
                date_requested=timezone.now()
            )
            # Set name and email for confirmation email
            user_name = faculty.user.get_full_name()
            user_email = faculty.user.email
        else:
            # User is neither student nor faculty (should not happen if login required)
            messages.error(request, "User profile not found.")
            return render(request, "students/requestform.html", {"student": None, "faculty": None, "id_number": ""})

        # Send confirmation email (common for both student and faculty)
        email_subject = 'Request Confirmation'
        email_body = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    margin: 0;
                    padding: 20px;
                    background-color: #f4f4f4;
                    text-align: center;
                }}
                .top-logo {{
                    margin-bottom: 20px;
                }}
                .top-logo img {{
                    max-width: 50px;
                }}
                .container {{
                    max-width: 500px;
                    margin: 0 auto;
                    background-color: #fff;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                    text-align: left;
                }}
                .title {{
                    text-align: center;
                    font-size: 24px;
                    color: #0056b3;
                    margin-bottom: 20px;
                    padding-bottom: 15px;
                    border-bottom: 1px solid #eee;
                }}
                p {{
                    margin-bottom: 15px;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    font-size: 12px;
                    color: #999;
                    text-align: center;
                    border-top: 1px solid #eee;
                }}
            </style>
        </head>
        <body>
            <div class="top-logo">
                <img src="https://i.ibb.co/0jZQZ9L/CTU-logo.png" alt="CTU Logo" style="max-width: 100px;">
            </div>

            <div class="container">
                <div class="title">REQUEST CONFIRMATION</div>

                <p>Dear <strong>{user_name}</strong>,</p>

                <p>Thank you for submitting your request for the document <strong>'{request_type}'</strong>. We have received it and our team is now processing it with utmost care and attention.</p>

                <p>Your request is currently being evaluated by our clinic nurse. You will receive another email once your document is approved.</p>

                <p>Best Regards,</p>
                <p><strong>CTU - Argao Campus Kahimsug Clinic Team</strong></p>
            </div>

            <div class="footer">
                <p>This is an automated message, please do not reply to this email.</p>
                <p>&copy; 2024 HealthHub Connect. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        if user_email:
            send_mail(
                email_subject,
                '',
                settings.EMAIL_HOST_USER,
                [user_email],
                html_message=email_body,
                fail_silently=False,
            )
        messages.success(request, "Request submitted. A confirmation email has been sent.")
        
        # Redirect to the correct dashboard based on user type
        if student_user:
            return redirect('main:main') # Redirect to main view which handles student dashboard redirection
        elif faculty_user:
             return redirect('main:main') # Redirect to main view which handles faculty dashboard redirection
        else:
             return redirect('main:main') # Fallback redirection
             
    # For GET requests, fetch the student or faculty object for initial form display
    student = get_student_by_user(request.user)
    faculty = get_faculty_by_user(request.user)
    id_number = ""
    if student:
        id_number = student.student_id
    elif faculty:
        id_number = faculty.faculty_id

    return render(request, "students/requestform.html", {"student": student, "faculty": faculty, "id_number": id_number})

# Views for medical requirements tracker
def student_medical_requirements_tracker(request):
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect('medical:upload_requirements')
    
    # Initialize variables to None at the start
    student = None
    faculty = None
    patient = None
    user = None # Explicitly initialize user
    med_requirements = None

    # Check for student_id or faculty_id in both POST and GET requests
    id_to_process = request.POST.get("id_number") or request.GET.get("id_number")

    # --- Handle POST requests for saving remarks or updating status ---
    if request.method == "POST" and id_to_process:
        action = request.POST.get('action')

        # --- Identify user and fetch record for POST ---
        try:
            # Try to find a Student first
            student = Student.objects.filter(student_id=id_to_process).first()
            if student:
                user = User.objects.get(email=student.email)
                patient = Patient.objects.get(user=user)
                med_requirements = MedicalRequirement.objects.filter(patient=patient).first()
                if not med_requirements:
                     messages.info(request, f"No medical requirements found for student ID {id_to_process}.")

            else:
                # If not a student, try to find a Faculty
                faculty = Faculty.objects.filter(faculty_id=id_to_process).first()
                if faculty:
                    user = faculty.user
                    med_requirements = MedicalRequirement.objects.filter(faculty=faculty).first()
                    if not med_requirements:
                         messages.info(request, f"No medical requirements found for faculty ID {id_to_process}.")
                else:
                    # If neither student nor faculty is found
                    messages.error(request, f"No student or faculty found with ID: {id_to_process}.")

        except (User.DoesNotExist, Patient.DoesNotExist, AttributeError) as e:
            messages.error(request, f"Error fetching user or patient for ID {id_to_process}: {e}")
            user = None # Ensure user is None on error
            patient = None # Ensure patient is None on error
            med_requirements = None # Ensure med_requirements is None on error

        # --- Process actions if record and user are found ---
        if med_requirements and user:
            try:
                if action == 'save_all_remarks':
                    x_ray_remarks = request.POST.get("x-ray-remark", "")
                    cbc_remarks = request.POST.get("cbc-remark", "")
                    drug_test_remarks = request.POST.get("drug-test-remark", "")
                    stool_examination_remarks = request.POST.get("stool-examination-remark", "")
                    pwd_card_remarks = request.POST.get("pwd-card-remark", "")

                    med_requirements.x_ray_remarks = x_ray_remarks
                    med_requirements.cbc_remarks = cbc_remarks
                    med_requirements.drug_test_remarks = drug_test_remarks
                    med_requirements.stool_examination_remarks = stool_examination_remarks
                    med_requirements.pwd_card_remarks = pwd_card_remarks

                    med_requirements.save()
                    messages.success(request, "Remarks saved successfully.")

                elif action in ['approve_requirements', 'reject_requirements']:
                    med_requirements.status = action.replace('_requirements', '') # 'approved' or 'rejected'
                    med_requirements.reviewed_by = request.user
                    med_requirements.reviewed_date = timezone.now()
                    med_requirements.save()
                    messages.success(request, f"Medical requirements marked as {med_requirements.status}.")

                    # Send email notification
                    recipient_email = user.email # Get email directly from the fetched user
                    recipient_name = user.get_full_name() or user.username

                    if recipient_email:
                        subject = f'Medical Requirements {med_requirements.status.capitalize()}'
                        status_text = "APPROVED" if action == 'approve_requirements' else "REJECTED"

                        email_body = render_to_string('email/medical_requirements_status.html', {
                            'med_requirements': med_requirements,
                            'recipient_name': recipient_name,
                            'status_text': status_text,
                        })

                        from django.core.mail import send_mail
                        from django.conf import settings

                        try:
                            send_mail(
                                subject,
                                '', # Empty plain text message
                                settings.DEFAULT_FROM_EMAIL,
                                [recipient_email],
                                html_message=email_body,
                                fail_silently=False,
                            )
                            messages.info(request, f"Email notification sent to {recipient_email}.")
                        except Exception as e:
                            messages.error(request, f"Failed to send email notification to {recipient_email}: {e}")

                    else:
                         # More specific message when email is not found for the identified user
                         messages.warning(request, f"Could not send email notification: Recipient email not found for user {user.username}.")

                    # Record transaction if requirements are approved
                    if action == 'approve_requirements':
                        # Determine the patient associated with the medical requirements
                        patient_for_transaction = None
                        if med_requirements.patient:
                            patient_for_transaction = med_requirements.patient
                        elif med_requirements.faculty:
                            # If linked to a faculty, try to find their patient record
                            try:
                                patient_for_transaction = Patient.objects.get(user=med_requirements.faculty.user)
                            except Patient.DoesNotExist:
                                # Create a patient record for the faculty if it doesn't exist
                                patient_for_transaction = Patient.objects.create(
                                    user=med_requirements.faculty.user,
                                    # Provide default values for required fields
                                    birth_date=None, age=0, weight=0, height=0, bloodtype='Unknown',
                                    allergies='None', medications='None', home_address='', city='',
                                    state_province='', postal_zipcode='', country='', nationality='',
                                    religion='', civil_status='', number_of_children=0, academic_year='',
                                    section='', parent_guardian='', parent_guardian_contact_number=''
                                )

                        if patient_for_transaction:
                            record_transaction(patient_for_transaction, "Medical Requirements Approval")
                            messages.success(request, "Transaction record created for Medical Requirements Approval.")
                        else:
                            messages.warning(request, "Could not create transaction record: Patient not found or created.")

            except Exception as e:
                 messages.error(request, f"An error occurred while processing the update: {e}")

        # Redirect to the same page with the ID to show updated data or error messages
        return redirect(f'{request.path}?id_number={id_to_process}')

    # --- Handle GET requests for searching or initial load ---
    if id_to_process and request.method == 'GET':
        try:
            # Explicitly try to find student or faculty first
            student = Student.objects.filter(student_id=id_to_process).first()
            if student:
                user = User.objects.get(email=student.email)
                patient = Patient.objects.get(user=user)
                med_requirements = MedicalRequirement.objects.filter(patient=patient).first()
                if not med_requirements:
                    messages.info(request, f"No medical requirements found for student ID {id_to_process}. Please upload the required documents.")

            else:
                # If not a student, try to find a Faculty
                faculty = Faculty.objects.filter(faculty_id=id_to_process).first()
                if faculty:
                    user = faculty.user
                    med_requirements = MedicalRequirement.objects.filter(faculty=faculty).first()
                    if not med_requirements:
                        messages.info(request, f"No medical requirements found for faculty ID {id_to_process}. Please upload the required documents.")

                else:
                    messages.error(request, f"No student or faculty found with ID Number: {id_to_process}.")

        except (User.DoesNotExist, Patient.DoesNotExist, AttributeError) as e:
             messages.error(request, f"Error fetching user or patient for ID {id_to_process}: {e}")
             student = None ; faculty = None; patient = None; user = None; med_requirements = None
        except Exception as e:
            messages.error(request, f"An unexpected error occurred during search: {e}")

    # If no id_number is provided (e.g., initial GET request to /medicalrequirementstracker/)
    # variables are already None from initialization, so just render the empty form.

    # Print statements for debugging (optional, remove in production)
    print("Rendering template with:")
    print("Student:", student)
    print("Faculty:", faculty)
    print("Patient:", patient)
    print("User:", user) # Print user object
    print("Medical Requirements:", med_requirements)
    print("ID to process:", id_to_process) # Print id_to_process

    return render(request, "medicalrequirements.html", {"med_requirements": med_requirements, "student": student, "patient": patient, "faculty": faculty, "id_number": id_to_process})

# Views for handling the medical requirements uploaded file
def upload_requirements(request):
    from main.models import Faculty
    requirements = [
        {'slug': 'chest_xray', 'name': 'Chest X-ray'},
        {'slug': 'cbc', 'name': 'Complete Blood Count (CBC)'},
        {'slug': 'drug_test', 'name': 'Drug Test'},
        {'slug': 'stool_examination', 'name': 'Stool Examination'},
        {'slug': 'pwd_card', 'name': 'PWD Card'}
    ]
    
    # Use helper functions to get student/faculty for the logged-in user
    student = get_student_by_user(request.user)
    faculty = get_faculty_by_user(request.user)

    patient = None
    md = None
    is_faculty = False
    id_number = ""
    mental_health_record = None

    if faculty:
        is_faculty = True
        id_number = faculty.faculty_id
        try:
            # Faculty upload logic: get or create medical records linked to faculty
            md, created_md = MedicalRequirement.objects.get_or_create(faculty=faculty)
            mental_health_record, created_mhr = MentalHealthRecord.objects.get_or_create(faculty=faculty)
        except Exception as e:
            messages.error(request, f"Error fetching/creating faculty medical records: {e}")
            # Decide how to handle this error, maybe return a different page or render with None
            return render(request, "students/medupload.html", {"requirements": requirements, "faculty": faculty, "is_faculty": is_faculty, "id_number": id_number})

    elif student:
        id_number = student.student_id
        try:
            # Student upload logic: find patient linked to the student's user
            user = request.user # Get the user from the request
            try:
                patient = Patient.objects.get(user=user)
            except Patient.DoesNotExist:
                messages.info(request, "Please complete your medical profile first.")
                # Redirect to the basic info page where patient profile can be created
                return redirect('medical:patient_basicinfo', student_id=student.student_id) 
                
            # If patient exists, get or create medical records linked to the patient
            md, created_md = MedicalRequirement.objects.get_or_create(patient=patient)
            mental_health_record, created_mhr = MentalHealthRecord.objects.get_or_create(patient=patient)

        except Exception as e:
            messages.error(request, f"Error fetching/creating student medical records: {e}")
            # Decide how to handle this error
            # Render the page with available data, even if some records failed to load
            pass # Continue to render the form with available data

    else:
        # Neither student nor faculty found for the logged-in user
        messages.error(request, "Profile not found. Please complete your profile first.")
        return render(request, "students/medupload.html", {"requirements": requirements, "student": None, "faculty": None, "id_number": id_number, "is_faculty": is_faculty}) # Render with empty profile info

    # Handle POST request for file uploads
    if request.method == "POST":
        # Check if the request is from the mental health availment form
        if 'avail_mental_health' in request.POST:
            avail_mental_health = request.POST.get('avail_mental_health')
            if mental_health_record:
                if avail_mental_health == 'yes':
                    mental_health_record.is_availing_mental_health = True
                    mental_health_record.save()
                    messages.success(request, "Your choice to avail Mental Health Services has been saved.", extra_tags='mental_health_availed')
                elif avail_mental_health == 'no':
                    mental_health_record.is_availing_mental_health = False
                    mental_health_record.save()
                    messages.success(request, "Your choice regarding Mental Health Services has been saved.")
            # Redirect back to the same page after saving the choice
            from django.urls import reverse
            base_url = reverse('medical:upload_requirements')
            if is_faculty:
                return redirect(f'{base_url}')
            elif student:
                return redirect(f'{base_url}?student_id={student.student_id}')
            else:
                 return redirect('main:login'); # Fallback

        # If not from the mental health form, assume it's from the file upload form
        else:
            uploaded_files_count = 0
            failed_uploads = {}
            allowed_content_types = [
                'application/pdf',
                'image/jpeg',
                'image/png',
                'image/gif',
            ]

            for input_name, file in request.FILES.items():
                if input_name.startswith('file_'):
                    requirement_slug = input_name.replace('file_', '')
                    valid_medical_slugs = [req['slug'] for req in requirements]
                    if requirement_slug in valid_medical_slugs:
                        if file.content_type not in allowed_content_types:
                            failed_uploads[file.name] = f"Invalid file type: {file.content_type}. Only PDF, JPG, JPEG, PNG, GIF are allowed."
                            messages.error(request, f"Invalid file type for {requirement_slug}: {file.name}.")
                            continue
                        try:
                            # Use md object obtained earlier
                            old_file = getattr(md, requirement_slug, None)
                            if old_file and hasattr(old_file, 'name') and old_file.name:
                                storage = old_file.storage
                                if storage.exists(old_file.name):
                                    storage.delete(old_file.name)
                            setattr(md, requirement_slug, file)
                            uploaded_files_count += 1
                            messages.success(request, f"{requirement_slug.replace('_', ' ').title()} uploaded successfully.")
                        except AttributeError:
                            failed_uploads[file.name] = f"MedicalRequirement model has no field for requirement slug: {requirement_slug}"
                            messages.error(request, f"Error uploading file for {requirement_slug}: Invalid requirement type.")
                        except Exception as e:
                            failed_uploads[file.name] = str(e)
                            messages.error(request, f"Error uploading file for {requirement_slug}: {e}")
                    elif requirement_slug in ['prescription', 'certification']:
                        if file.content_type not in allowed_content_types:
                            failed_uploads[file.name] = f"Invalid file type: {file.content_type}. Only PDF, JPG, JPEG, PNG, GIF are allowed."
                            messages.error(request, f"Invalid file type for {requirement_slug}: {file.name}.")
                            continue
                        try:
                            # Use mental_health_record object obtained earlier
                            old_file = getattr(mental_health_record, requirement_slug, None)
                            if old_file and hasattr(old_file, 'name') and old_file.name:
                                storage = old_file.storage
                                if storage.exists(old_file.name):
                                    storage.delete(old_file.name)
                            setattr(mental_health_record, requirement_slug, file)
                            uploaded_files_count += 1
                            messages.success(request, f"Mental Health {requirement_slug.replace('_', ' ').title()} uploaded successfully.")
                        except AttributeError:
                            failed_uploads[file.name] = f"MentalHealthRecord model has no field for: {requirement_slug}"
                            messages.error(request, f"Error uploading file for {requirement_slug}: Invalid document type.")
                        except Exception as e:
                            failed_uploads[file.name] = str(e)
                            messages.error(request, f"Error uploading file for {requirement_slug}: {e}")
            if uploaded_files_count > 0:
                try:
                    md_modified = any(name.startswith('file_') and name.replace('file_', '') in [req['slug'] for req in requirements] for name in request.FILES.keys())
                    mhr_modified = any(name.startswith('file_') and name.replace('file_', '') in ['prescription', 'certification'] for name in request.FILES.keys())
                    if md_modified:
                        md.save()
                    if mhr_modified:
                        mental_health_record.save()
                except Exception as e:
                    messages.error(request, f"Error saving records: {e}")
            if not uploaded_files_count and not failed_uploads:
                messages.info(request, "No files were selected for upload.")
            elif failed_uploads:
                messages.warning(request, f"Some files failed to upload: {failed_uploads}")
            from django.urls import reverse
            base_url = reverse('medical:upload_requirements')
            if is_faculty:
                return redirect(f'{base_url}')
            elif student:
                # Use student.student_id from the retrieved student object
                return redirect(f'{base_url}?student_id={student.student_id}')
            else:
                 # Fallback if neither student nor faculty is found (shouldn't happen if initial checks work)
                 return redirect('main:login'); # Or another appropriate fallback
    return render(request, "students/medupload.html", {"requirements": requirements, "md": md, "patient": patient, "mental_health_record": mental_health_record, "student": student, "faculty": faculty, "is_faculty": is_faculty, "id_number": id_number})

# Custom template filter for basename
def basename(value):
    import os
    return os.path.basename(value)

from django import template
register = template.Library()
register.filter('basename', basename)

# Views for handling students request for dental services
def dental_services(request):
    # Common variables for both admin and regular users
    id_number = None
    student = None
    faculty = None

    # Handle staff/superuser differently - they manage the system
    if request.user.is_superuser or request.user.is_staff:
        if request.method == "POST":
            service_type = request.POST.get("service_type")
            student_id = request.POST.get("student_id")  # Get the student ID for whom the request is being made
            
            if not service_type:
                messages.error(request, "Please select a service type")
                return render(request, "students/dentalrequestform.html", {"id_number": id_number, "student": student, "faculty": faculty})

            if not student_id:
                messages.error(request, "Please enter a student ID")
                return render(request, "students/dentalrequestform.html", {"id_number": id_number, "student": student, "faculty": faculty})

            try:
                # Get the student and their associated patient
                student = Student.objects.get(student_id=student_id)
                user = User.objects.get(email=student.email)
                patient = Patient.objects.get(user=user)

                # Check if the student already has a pending request for this service type
                dental_service_request = DentalRecords.objects.filter(patient=patient, service_type=service_type)
                if dental_service_request.exists():
                    messages.error(request, f"Student {student_id} already has a pending request for this service")
                    return render(request, "students/dentalrequestform.html", {"id_number": id_number, "student": student, "faculty": faculty})

                # Create dental service request for the student
                dental_request = DentalRecords.objects.create(
                    patient=patient,
                    service_type=service_type,
                    date_requested=timezone.now(),
                    created_by=request.user  # Track which staff member created the request
                )

                # Send confirmation email to the student
                email_subject = 'Dental Services Request Submitted'
                html_message = render_to_string('email/dental_request_confirmation.html', {
                    'patient_name': f"{student.firstname} {student.lastname}",
                    'service_type': service_type,
                })

                send_mail(
                    email_subject,
                    '',
                    settings.EMAIL_HOST_USER,
                    [student.email],
                    html_message=html_message,
                    fail_silently=False,
                )

                messages.success(request, f"Dental service request created successfully for student {student_id}")
                return render(request, "students/dentalrequestform.html", {"id_number": id_number, "student": student, "faculty": faculty})

            except Student.DoesNotExist:
                messages.error(request, f"Student with ID {student_id} not found")
                return render(request, "students/dentalrequestform.html", {"id_number": id_number, "student": student, "faculty": faculty})
            except Patient.DoesNotExist:
                messages.error(request, f"Student {student_id} has not completed their medical profile")
                return render(request, "students/dentalrequestform.html", {"id_number": id_number, "student": student, "faculty": faculty})
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
                return render(request, "students/dentalrequestform.html", {"id_number": id_number, "student": student, "faculty": faculty})

        # For GET requests from staff/superuser
        return render(request, "students/dentalrequestform.html", {
            "id_number": id_number,
            "student": student,
            "faculty": faculty,
            "is_staff": True  # Add this flag to show staff-specific UI elements
        })

    # Original logic for regular users (students/faculty)
    student = get_student_by_user(request.user)
    faculty = get_faculty_by_user(request.user)
    if faculty:
        id_number = faculty.faculty_id
    elif student:
        id_number = student.student_id
    else:
        id_number = ""

    if request.method == "POST":
        # Get the patient profile for the logged-in user
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            messages.info(request, "Please complete your medical profile first.")
            logged_in_student = get_student_by_user(request.user)
            if logged_in_student:
                return redirect('medical:patient_basicinfo', student_id=logged_in_student.student_id)
            else:
                messages.error(request, "Cannot access dental services without a patient profile.")
                return redirect('main:main')

        service_type = request.POST.get("service_type")
        if not service_type:
            messages.error(request, "Please select a service type")
            return render(request, "students/dentalrequestform.html", {"id_number": id_number, "student": student, "faculty": faculty})

        # Check if the user (patient) already has a pending request for this service type
        dental_service_request = DentalRecords.objects.filter(patient=patient, service_type=service_type)
        if dental_service_request.exists():
            messages.error(request, "You have already requested this type of service")
            return render(request, "students/dentalrequestform.html", {"id_number": id_number, "student": student, "faculty": faculty})

        # Create dental service request object linked to the patient
        dental_request = DentalRecords.objects.create(
            patient=patient,
            service_type=service_type,
            date_requested=timezone.now()
        )

        # Send confirmation email to the user
        user_email = request.user.email
        user_name = request.user.get_full_name() or request.user.username

        email_subject = 'Dental Services Request Submitted'
        html_message = render_to_string('email/dental_request_confirmation.html', {
            'patient_name': user_name,
            'service_type': service_type,
        })

        send_mail(
            email_subject,
            '',
            settings.EMAIL_HOST_USER,
            [user_email],
            html_message=html_message,
            fail_silently=False,
        )

        messages.success(request, "Request submitted. A confirmation email has been sent.")
        return render(request, "students/dentalrequestform.html", {"id_number": id_number, "student": student, "faculty": faculty})

    # For GET request, render the initial form
    return render(request, "students/dentalrequestform.html", {"id_number": id_number, "student": student, "faculty": faculty})

# Views for appointing students dental requests
def dental_request(request):
    if request.user.is_superuser or request.user.is_staff:
        if request.method == "POST":
            request_id = request.POST.get("request_id")
            appointment_date_str = request.POST.get("appointment_date")
            appointment_time_str = request.POST.get("appointment_time")

            try:
                # Get the DentalRecords object
                dental_record = DentalRecords.objects.get(id=request_id)

                # Combine date and time strings and convert to datetime object
                # Need to import datetime and timezone
                from datetime import datetime
                from django.utils import timezone

                appointment_datetime = datetime.strptime(f"{appointment_date_str} {appointment_time_str}", "%Y-%m-%d %H:%M")
                # Make the datetime timezone-aware
                appointment_datetime = timezone.make_aware(appointment_datetime)

                # Update the dental record
                dental_record.date_appointed = appointment_datetime
                dental_record.appointed = True
                dental_record.save()

                messages.success(request, "Appointment set successfully.")

            except DentalRecords.DoesNotExist:
                messages.error(request, "Dental request not found.")
            except ValueError:
                messages.error(request, "Invalid date or time format.")
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")

            # Redirect or refresh the page after processing
            # return redirect('medical:dental_request') # Assuming 'medical:dental_request' is the URL name for this view

        service_request = DentalRecords.objects.filter(appointed=False).select_related('patient__user')
        
        # Fetch and attach ID and name to each request for either student or faculty
        for request_item in service_request:
            request_item.user_id = "N/A"
            request_item.user_name = "N/A"

            if request_item.patient and request_item.patient.user:
                user = request_item.patient.user
                
                # Try to get Student info
                try:
                    student = Student.objects.get(email=user.email)
                    request_item.user_id = student.student_id
                    request_item.user_name = f"{student.lastname}, {student.firstname}"
                except Student.DoesNotExist:
                    # If not a student, try to get Faculty info
                    try:
                        faculty = Faculty.objects.get(user=user)
                        request_item.user_id = faculty.faculty_id
                        request_item.user_name = f"{faculty.user.last_name}, {faculty.user.first_name}"
                    except Faculty.DoesNotExist:
                        # User is neither student nor faculty (or not linked properly)
                        request_item.user_id = "User ID N/A"
                        request_item.user_name = user.get_full_name() or user.username or "Unknown User"
            else:  # Handle cases where patient or user might be missing on DentalRecord
                 request_item.user_id = "N/A"
                 request_item.user_name = "Patient/User Missing"

    return render(request, "admin/dentalrequest.html", {"service_request": service_request})

# View dental schedules
def dental_schedule(request):
    if request.user.is_superuser or request.user.is_staff:
        schedules = DentalRecords.objects.filter(appointed=True).select_related('patient__user')
        
        # Attach ID and name to each schedule for either student or faculty
        for schedule in schedules:
            schedule.id_number = "N/A"
            schedule.lastname = "N/A"
            schedule.firstname = "N/A"

            if schedule.patient and schedule.patient.user:
                user = schedule.patient.user

                # Try to get Student info
                try:
                    student = Student.objects.get(email=user.email)
                    schedule.id_number = student.student_id
                    schedule.lastname = student.lastname
                    schedule.firstname = student.firstname
                except Student.DoesNotExist:
                    # If not a student, try to get Faculty info
                    try:
                        faculty = Faculty.objects.get(user=user)
                        schedule.id_number = faculty.faculty_id
                        schedule.lastname = faculty.user.last_name
                        schedule.firstname = faculty.user.first_name
                    except Faculty.DoesNotExist:
                        # User is neither student nor faculty (or not linked properly)
                        schedule.id_number = "User ID N/A"
                        schedule.lastname = "Unknown"
                        schedule.firstname = "User"
            else:  # Handle cases where patient or user might be missing on DentalRecord
                schedule.id_number = "N/A"
                schedule.lastname = "Patient/User"
                schedule.firstname = "Missing"

        if request.method == "POST":
            action = request.POST.get("action")

            if action == "done":
                request_id = request.POST.get("request_id") # Use request_id from the form
                
                try:
                    dental_record = DentalRecords.objects.get(id=request_id)

                    # Create a TransactionRecord
                    # Ensure patient is not None before creating transaction
                    if dental_record.patient:
                         TransactionRecord.objects.create(
                            patient=dental_record.patient,
                            transac_type=dental_record.service_type,
                            transac_date=timezone.now()
                        )
                         messages.success(request, "Transaction recorded successfully.")
                    else:
                         messages.warning(request, "Cannot record transaction: Patient not linked to dental record.")

                    # Delete the dental record after marking as done
                    dental_record.delete()

                    messages.success(request, "Marked As Done")

                except DentalRecords.DoesNotExist:
                    messages.error(request, "Dental record not found.")
                except Exception as e:
                    messages.error(request, f"An error occurred: {str(e)}")

                # Redirect or re-render after processing
                return redirect('medical:dentalschedule') # Redirect back to the schedule page

            elif action == "reschedule":
                request_id = request.POST.get("request_id")
                str_appointment_date = request.POST.get("new_appointment_date")
                str_appointment_time = request.POST.get("new_appointment_time")

                try:
                    dental_record = DentalRecords.objects.get(id=request_id)

                    if not str_appointment_date or not str_appointment_time:
                        raise ValueError("New appointment date and time are required")

                    # Combine date and time strings into a datetime object
                    new_appointment_datetime = datetime.strptime(f"{str_appointment_date} {str_appointment_time}", "%Y-%m-%d %H:%M")

                    # Convert new appointment datetime to the current timezone
                    new_appointment_datetime = timezone.make_aware(new_appointment_datetime)

                    dental_record.date_appointed = new_appointment_datetime
                    dental_record.save()

                    # Get user info for email
                    user = None
                    recipient_name = ""
                    recipient_email = ""
                    
                    if dental_record.patient and dental_record.patient.user:
                        user = dental_record.patient.user
                        try:
                            student = Student.objects.get(email=user.email)
                            recipient_name = f"{student.firstname} {student.lastname}"
                            recipient_email = student.email
                        except Student.DoesNotExist:
                            try:
                                faculty = Faculty.objects.get(user=user)
                                recipient_name = faculty.user.get_full_name()
                                recipient_email = faculty.user.email
                            except Faculty.DoesNotExist:
                                recipient_name = user.get_full_name() or user.username
                                recipient_email = user.email

                    if recipient_email:
                        email_subject = 'Dental Appointment Rescheduled'
                        html_message = render_to_string('email/dental_reschedule_email.html', {
                            'patient_name': recipient_name,
                            'service_type': dental_record.service_type,
                            'new_appointment_datetime': new_appointment_datetime,
                        })

                        send_mail(
                            email_subject,
                            '', # Plain text message is empty as we send HTML
                            settings.EMAIL_HOST_USER,
                            [recipient_email],
                            html_message=html_message,
                            fail_silently=False,
                        )

                    messages.success(request, "Appointment rescheduled successfully. Email sent.")
                except DentalRecords.DoesNotExist:
                    messages.error(request, "Dental record not found.")
                except ValueError as e:
                    messages.error(request, str(e))
                except Exception as e:
                    messages.error(request, f"An error occurred: {str(e)}")

        return render(request, "admin/dentalschedule.html", {"schedules": schedules})
    else:
        return HttpResponseForbidden("You don't have permission to access this page.")

# List pwd
@user_passes_test(is_admin)
def pwd_list(request):
    if request.user.is_superuser or request.user.is_staff:
        # Filter patients who have both PWD status and medical requirements
        pwd_patients = Patient.objects.filter(
            riskassessment__pwd=True,
            medicalrequirement__isnull=False
        ).select_related(
            'user__faculty', 
            'user', 
            'medicalclearance__riskassessment',
            'medicalrequirement'
        )

        # Attach the correct ID (Student ID or Faculty ID) and potentially the related student/faculty object
        # to each patient object for easier access in the template.
        for patient in pwd_patients:
            patient.user_id_display = "N/A"
            patient.related_student = None
            patient.related_faculty = None

            # Get the related MedicalRequirement for this patient (already prefetched)
            medical_requirement = patient.medicalrequirement
            patient.pwd_file = medical_requirement.pwd_card if medical_requirement else None

            # Access risk assessment directly if pre-fetched via medicalclearance
            patient.risk_assessment_obj = None
            if hasattr(patient, 'medicalclearance') and hasattr(patient.medicalclearance, 'riskassessment'):
                patient.risk_assessment_obj = patient.medicalclearance.riskassessment

            patient.remarks_display = "N/A"

            if patient.user:
                try:
                    # Try to get student first by user's email
                    student = Student.objects.filter(email=patient.user.email).first()
                    if student:
                        patient.user_id_display = student.student_id
                        patient.related_student = student
                except Exception:
                    pass

                if not patient.related_student:
                    # If not a student, check for faculty (already select_related)
                    if hasattr(patient.user, 'faculty') and patient.user.faculty:
                        faculty = patient.user.faculty
                        patient.user_id_display = faculty.faculty_id
                        patient.related_faculty = faculty

            # Set remarks display if RiskAssessment is found
            if patient.risk_assessment_obj and patient.risk_assessment_obj.disability:
                patient.remarks_display = patient.risk_assessment_obj.disability

        if request.method == "POST":
            search_id = request.POST.get("student_id")
            filtered_pwd_patients = []
            if search_id:
                # Filter by the attached user_id_display
                for patient in pwd_patients:
                    if patient.user_id_display == search_id:
                        filtered_pwd_patients.append(patient)

                if not filtered_pwd_patients:
                    messages.error(request, f"No PWD student or faculty found with ID: {search_id}")

                pwd_patients = filtered_pwd_patients

        return render(request, "admin/pwdlist.html", {"pwds": pwd_patients})
    else:
        return HttpResponseForbidden("You don't have permission to access this page.")
        
# View pwd in details
def pwd_detail(request, id):
    if not request.user.is_superuser and not request.user.is_staff:
        return HttpResponseForbidden("You don't have permission to access this page.")

    student = None
    faculty = None
    user = None
    patient = None
    md = None

    try:
        # Try to find a Student first
        student = Student.objects.filter(student_id=id).first()
        if student:
            user = User.objects.get(email=student.email)

        # If not a student, try to find a Faculty
        if not user:
            faculty = Faculty.objects.filter(faculty_id=id).first()
            if faculty:
                user = faculty.user

        # If neither student nor faculty was found with the provided ID
        if not user:
            messages.error(request, f"No student or faculty found with ID: {id}")
            return redirect('medical:pwdlist')

        # Get the patient record for the user
        try:
            patient = Patient.objects.get(user=user)
        except Patient.DoesNotExist:
            messages.error(request, f"Patient record not found for user {user.get_full_name() or user.username} (ID: {id}).")
            return redirect('medical:pwdlist')

        # Get the medical requirements for the patient
        try:
             md = MedicalRequirement.objects.get(patient=patient)
        except MedicalRequirement.DoesNotExist:
             messages.error(request, f"Medical Requirements record not found for patient {patient.user.get_full_name() or patient.user.username} (ID: {id}).")
             return redirect('medical:pwdlist')

    except User.DoesNotExist:
        messages.error(request, f"User account not found for ID: {id}.")
        return redirect('medical:pwdlist')
    except Patient.DoesNotExist:
         messages.error(request, f"Patient record not found for ID: {id}.")
         return redirect('medical:pwdlist')
    except Exception as e:
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return redirect('medical:pwdlist')

    # Pass all relevant objects to the template
    context = {
        'patient': patient,
        'student': student,  # Pass student object if found
        'faculty': faculty,  # Pass faculty object if found
        'md': md
    }

    return render(request, 'admin/pwddetails.html', context)


@user_passes_test(is_admin)
def verify_pwd(request, id):
    if request.method == "POST":
        try:
            user = None
            # Try to find a Student first
            student = Student.objects.filter(student_id=id).first()
            if student:
                user = User.objects.get(email=student.email)
            else:
                # If not a student, try to find a Faculty
                faculty = Faculty.objects.filter(faculty_id=id).first()
                if faculty:
                    user = faculty.user

            if not user:
                messages.error(request, f"No user found with ID: {id}.")
                return redirect('medical:pwdlist')

            patient = Patient.objects.get(user=user)

            # Get or create MedicalClearance for the patient
            # Get or create MedicalClearance for the patient using patient's primary key
            # Using patient_id=patient.pk might circumvent TypeError with Patient object instance lookup
            medical_clearance, created = MedicalClearance.objects.get_or_create(patient_id=patient.pk)

            # Get RiskAssessment through MedicalClearance.
            # If not found directly linked to *this* MedicalClearance, try to find one linked to it with pwd=True.
            try:
                risk_assessment = medical_clearance.riskassessment
            except RiskAssessment.DoesNotExist:
                 # Try finding RiskAssessment linked to the medical_clearance we just got/created, filtered by pwd=True
                 try:
                     risk_assessment = RiskAssessment.objects.get(clearance=medical_clearance, pwd=True)
                 except RiskAssessment.DoesNotExist:
                     # If RiskAssessment is still not found linked to this medical clearance,
                     # it indicates that the PWD RiskAssessment record for this patient is missing or not linked correctly.
                     messages.error(request, f"Risk Assessment record with PWD status not found for patient {patient.user.get_full_name() or patient.user.username}. Cannot verify PWD status. Please ensure a Risk Assessment with PWD status exists and is linked to the Medical Clearance.")
                     return redirect('medical:pwdlist')


            # Proceed with verification
            risk_assessment.pwd_verified = True
            risk_assessment.pwd_verification_date = timezone.now()
            risk_assessment.pwd_verified_by = request.user
            risk_assessment.save()

            user_name = user.get_full_name() or user.username
            messages.success(request, f"PWD status has been verified for {user_name}.")

            # Record the transaction
            record_transaction(patient, "PWD Verification")

        except (Student.DoesNotExist, Faculty.DoesNotExist, User.DoesNotExist, Patient.DoesNotExist) as e:
            messages.error(request, f"Error finding patient or user for ID {id}: {str(e)}")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {str(e)}")

        return redirect('medical:pwdlist')

@user_passes_test(is_admin)
def unverify_pwd(request, id):
    if request.method == "POST":
        try:
            user = None
            # Try to find a Student first
            student = Student.objects.filter(student_id=id).first()
            if student:
                user = User.objects.get(email=student.email)
            else:
                # If not a student, try to find a Faculty
                faculty = Faculty.objects.filter(faculty_id=id).first()
                if faculty:
                    user = faculty.user

            if not user:
                messages.error(request, f"No user found with ID: {id}.")
                return redirect('medical:pwdlist')

            patient = Patient.objects.get(user=user)

            # Get or create MedicalClearance for the patient
            # Explicitly ensure patient is a Patient instance before passing
            if isinstance(patient, Patient):
                medical_clearance, created = MedicalClearance.objects.get_or_create(patient=patient)
            else:
                # This case should ideally not be reached if Patient.objects.get works as expected
                messages.error(request, f"Internal Error: Retrieved object for user {user.username} is not a Patient instance.")
                return redirect('medical:pwdlist')

            # Get RiskAssessment through MedicalClearance.
            # If not found directly linked to *this* MedicalClearance, try to find one linked to it with pwd=True.
            try:
                risk_assessment = medical_clearance.riskassessment
            except RiskAssessment.DoesNotExist:
                # Try finding RiskAssessment linked to the medical_clearance we just got/created, filtered by pwd=True
                try:
                    risk_assessment = RiskAssessment.objects.get(clearance=medical_clearance, pwd=True)
                except RiskAssessment.DoesNotExist:
                    # If RiskAssessment is still not found linked to this medical clearance,
                    # it indicates that the PWD RiskAssessment record for this patient is missing or not linked correctly.
                    messages.error(request, f"Risk Assessment record with PWD status not found for patient {patient.user.get_full_name() or patient.user.username}. Cannot unverify PWD status. Please ensure a Risk Assessment with PWD status exists and is linked to the Medical Clearance.")
                    return redirect('medical:pwdlist')


            # Proceed with unverification
            risk_assessment.pwd_verified = False
            risk_assessment.pwd_verification_date = None
            risk_assessment.pwd_verified_by = None
            risk_assessment.save()

            user_name = user.get_full_name() or user.username
            messages.success(request, f"PWD status has been unverified for {user_name}.")

            # Record the transaction
            record_transaction(patient, "PWD Unverification")

        except (Student.DoesNotExist, Faculty.DoesNotExist, User.DoesNotExist, Patient.DoesNotExist) as e:
            messages.error(request, f"Error finding patient or user for ID {id}: {str(e)}")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {str(e)}")

        return redirect('medical:pwdlist')
# List all record of prescriptions
def view_prescription_records(request):
    if not request.user.is_superuser and not request.user.is_staff:
        return HttpResponseForbidden("You don't have permission to access this page.")
    # Fetch all prescription records and select related patient and user
    presc_record = PrescriptionRecord.objects.all().select_related('patient__user').order_by('-date_prescribed') # Order by date as well

    # Attach the correct ID (Student ID or Faculty ID) and name to each record
    for prescription in presc_record:
        prescription.user_id_display = "N/A"
        prescription.user_name_display = prescription.name # Use the name saved in the record by default

        if prescription.patient and prescription.patient.user:
            user = prescription.patient.user
            try:
                # Try to get student first by user's email
                student = Student.objects.filter(email=user.email).first()
                if student:
                    prescription.user_id_display = student.student_id
                    # Update name display if needed, though the saved name should be correct now
                    # prescription.user_name_display = f"{student.firstname} {student.lastname}".title()
                else:
                    # If not a student, try to get faculty by user
                    faculty = Faculty.objects.filter(user=user).first()
                    if faculty:
                        prescription.user_id_display = faculty.faculty_id
                        # prescription.user_name_display = faculty.user.get_full_name() or faculty.user.username
                    # If neither student nor faculty found, ID remains "N/A"
            except Exception as e:
                # Handle potential errors during lookup
                prescription.user_id_display = f"Error: {e}"
                # Keep the saved name in case of lookup error

    return render(request, "admin/prescriptionrecords.html", {"prescription_records": presc_record})

# List all record of emergency health assistance
def view_emergency_health_records(request):
    if not request.user.is_superuser and not request.user.is_staff:
        return HttpResponseForbidden("You don't have permission to access this page.")
    emrgncy_records = EmergencyHealthAssistanceRecord.objects.all().select_related('patient__user')

    # Attach the correct ID (Student ID or Faculty ID) to each record
    for record in emrgncy_records:
        record.user_id_display = "N/A"
        if record.patient and record.patient.user:
            try:
                # Try to get student first by user's email
                student = Student.objects.filter(email=record.patient.user.email).first()
                if student:
                    record.user_id_display = student.student_id
                else:
                    # If not a student, try to get faculty by user
                    faculty = Faculty.objects.filter(user=record.patient.user).first()
                    if faculty:
                        record.user_id_display = faculty.faculty_id
                    # If neither student nor faculty found, ID remains "N/A"
            except Exception as e:
                # Handle potential errors during lookup
                record.user_id_display = f"Error: {e}"

    return render(request, "admin/emergencyhealthrecords.html", {"emrgncy_record": emrgncy_records})

# Check if eligible for insurance
def check_insurance_availability(request):
    if request.method == "POST":
        student_id = request.POST.get("student_id")

        if EmergencyHealthAssistanceRecord.objects.filter(patient__student__student_id = student_id).exists():
            messages.success(request, "Done checking, you are eligible for an insurance")
            return render(request, "students/emergencyinsurance.html", {"eligible": True})
        else:
            messages.error(request, "Done checking, you are not eligible for an insurance")
            return render(request, "students/emergencyinsurance.html", {})
    return render(request, "students'/emergencyinsurance.html", {})

# Views for handling transactions
def transactions_view(request):
    transaction_type = request.GET.get('type', 'all')
    # Only select_related for patient and user
    transaction_records = TransactionRecord.objects.all().select_related('patient__user')

    if transaction_type != 'all':
        if transaction_type == 'Medical Document Request':
            transaction_records = transaction_records.filter(transac_type__startswith='Medical Document Request')
        elif transaction_type == 'Dental Service':
            # Include all specific dental service types
            dental_service_types = ['Cleaning', 'Dental Filling', 'Tooth Extraction']
            transaction_records = transaction_records.filter(transac_type__in=dental_service_types)
        else:
            transaction_records = transaction_records.filter(transac_type=transaction_type)

    # Order by date, most recent first
    transaction_records = transaction_records.order_by('-transac_date')

    # Get IDs for each record
    for record in transaction_records:
        if record.patient and record.patient.user:
            try:
                # Try to get student first
                student = Student.objects.filter(email=record.patient.user.email).first()
                if student:
                    record.student_id = student.student_id
                else:
                    # If not a student, try to get faculty
                    faculty = Faculty.objects.filter(user=record.patient.user).first()
                    if faculty:
                        record.student_id = faculty.faculty_id
                    else:
                        record.student_id = "N/A"
            except Exception:
                record.student_id = "N/A"

    return render(request, 'admin/transactions.html', {
        'transaction_records': transaction_records,
        'transaction_type': transaction_type,
        'filter_option': 'all'
    })

def monthly_transactions_view(request):
    if request.method == 'POST':
        selected_month = request.POST.get('selected_month')
        selected_year = request.POST.get('selected_year')
        transaction_type = request.POST.get('type', 'all')

        # Only select_related for patient and user
        transaction_records = TransactionRecord.objects.all().select_related('patient__user')

        if selected_month and selected_year:
            selected_month = int(selected_month)
            selected_year = int(selected_year)
            transaction_records = transaction_records.filter(
                transac_date__month=selected_month,
                transac_date__year=selected_year
            )

        if transaction_type != 'all':
            if transaction_type == 'Medical Document Request':
                transaction_records = transaction_records.filter(transac_type__startswith='Medical Document Request')
            else:
                transaction_records = transaction_records.filter(transac_type=transaction_type)

        # Order by date, most recent first
        transaction_records = transaction_records.order_by('-transac_date')

        # Get IDs for each record
        for record in transaction_records:
            if record.patient and record.patient.user:
                try:
                    # Try to get student first
                    student = Student.objects.filter(email=record.patient.user.email).first()
                    if student:
                        record.student_id = student.student_id
                    else:
                        # If not a student, try to get faculty
                        faculty = Faculty.objects.filter(user=record.patient.user).first()
                        if faculty:
                            record.student_id = faculty.faculty_id
                        else:
                            record.student_id = "N/A"
                except Exception:
                    record.student_id = "N/A"

        return render(request, 'admin/transactions.html', {
            'transaction_records': transaction_records,
            'filter_option': 'monthly',
            'selected_month': selected_month,
            'selected_year': selected_year,
            'transaction_type': transaction_type,
        })
    else:
        selected_month = request.GET.get('month')
        selected_year = request.GET.get('year')
        transaction_type = request.GET.get('type', 'all')

        # Only select_related for patient and user
        transaction_records = TransactionRecord.objects.all().select_related('patient__user')

        if selected_month and selected_year:
            selected_month = int(selected_month)
            selected_year = int(selected_year)
            transaction_records = transaction_records.filter(
                transac_date__month=selected_month,
                transac_date__year=selected_year
            )

        if transaction_type != 'all':
            if transaction_type == 'Medical Document Request':
                transaction_records = transaction_records.filter(transac_type__startswith='Medical Document Request')
            else:
                transaction_records = transaction_records.filter(transac_type=transaction_type)

        # Order by date, most recent first
        transaction_records = transaction_records.order_by('-transac_date')

        # Get IDs for each record
        for record in transaction_records:
            if record.patient and record.patient.user:
                try:
                    # Try to get student first
                    student = Student.objects.filter(email=record.patient.user.email).first()
                    if student:
                        record.student_id = student.student_id
                    else:
                        # If not a student, try to get faculty
                        faculty = Faculty.objects.filter(user=record.patient.user).first()
                        if faculty:
                            record.student_id = faculty.faculty_id
                        else:
                            record.student_id = "N/A"
                except Exception:
                    record.student_id = "N/A"

        month_name = calendar.month_name[selected_month]
        return render(request, 'admin/transactions.html', {
            'transaction_records': transaction_records,
            'filter_option': 'monthly',
            'selected_month': selected_month,
            'selected_year': selected_year,
            'transaction_type': transaction_type,
            'month_name': month_name,
            'monthly': True
        })

def daily_transactions_view(request):
    transaction_type = request.GET.get('type', 'all')
    
    # Only select_related for patient and user
    transaction_records = TransactionRecord.objects.filter(
        transac_date__date=date.today()
    ).select_related('patient__user')

    if transaction_type != 'all':
        if transaction_type == 'Medical Document Request':
            transaction_records = transaction_records.filter(transac_type__startswith='Medical Document Request')
        else:
            transaction_records = transaction_records.filter(transac_type=transaction_type)

    # Order by date, most recent first
    transaction_records = transaction_records.order_by('-transac_date')

    # Get IDs for each record
    for record in transaction_records:
        if record.patient and record.patient.user:
            try:
                # Try to get student first
                student = Student.objects.filter(email=record.patient.user.email).first()
                if student:
                    record.student_id = student.student_id
                else:
                    # If not a student, try to get faculty
                    faculty = Faculty.objects.filter(user=record.patient.user).first()
                    if faculty:
                        record.student_id = faculty.faculty_id
                    else:
                        record.student_id = "N/A"
            except Exception:
                record.student_id = "N/A"

    today = date.today()
    month_name = calendar.month_name[today.month]

    return render(request, 'admin/transactions.html', {
        'transaction_records': transaction_records,
        'transaction_type': transaction_type,
        'month_name': month_name,
        'date_today': today.day,
        'year': today.year,
        'daily': True
    })

# def med_certificate_for_intrams(request, student_id):
#     if request.user.is_superuser or request.user.is_staff:
#         if request.method == "POST":
#             #student_request = StudentRequest.objects.get(student__student_id = student_id, request_type = "Medical Certificate for Intramurals")
#             #student_request.date_approved = datetime.now()
#             #student_request.save()
#             return render(request, "admin/med_cert.html", {"approve": True})
#         student = Student.objects.get(student_id=student_id)
#         messages.info(request, f"Issue Medical Certificate for {student.firstname.title()}")
#         return render(request, "admin/med_cert.html", {"student": student})
#     else:
#         return HttpResponseForbidden("You don't have permission to access this page.")

def med_cert(request, student_id):
    if not request.user.is_superuser and not request.user.is_staff:
        return HttpResponseForbidden("You don't have permission to access this page.")
    student = Student.objects.get(student_id=student_id)
    user = User.objects.get(email=student.email)
    patient = Patient.objects.get(user=user)

    if request.method == "POST":
        college = request.POST.get("college")
        year = request.POST.get("year")
        age = request.POST.get("age")
        height = request.POST.get("height")
        weight = request.POST.get("weight")
        bp = request.POST.get("bp")
        p = request.POST.get("p")
        t = request.POST.get("t")
        rr = request.POST.get("rr")
        sports_played = request.POST.get("sports_played")
        physically_able = request.POST.get("able") == "on"
        print(physically_able)
        physically_not_able = request.POST.get("not-able") == "on"

        # Check if MedicalCertificate exists for the fetched patient
        if MedicalCertificate.objects.filter(patient=patient).exists():
            med_cert = MedicalCertificate.objects.get(patient=patient)
            med_cert.college = college
            med_cert.year = year
            med_cert.age = age
            med_cert.height = height
            med_cert.weight = weight
            med_cert.bp = bp
            med_cert.p = p
            med_cert.t = t
            med_cert.rr = rr
            med_cert.sports_played = sports_played
            med_cert.physically_able = physically_able
            med_cert.physically_not_able = physically_not_able
            med_cert.save()

            messages.success(request, "Record Updated")
            return render(request, "admin/med_cert.html", {"patient": patient, "cedicalcertificate": med_cert})
        
        med_cert = MedicalCertificate.objects.create(
            patient = patient,
            college = college,
            year = year,
            age = age,
            height = height,
            weight = weight,
            bp = bp,
            p = p,
            t = t,
            rr = rr,
            sports_played = sports_played,
            physically_able = physically_able,
            physically_not_able = physically_not_able
        )
        messages.success(request, "Medical certificate successfully created")
        return render(request, "admin/med_cert.html", {"patient": patient, "cedicalcertificate": med_cert})
    # For GET request, check if MedicalCertificate exists for the fetched patient
    if MedicalCertificate.objects.filter(patient=patient).exists():
        med_cert = MedicalCertificate.objects.get(patient=patient)
        return render(request, "admin/med_cert.html", {"patient": patient, "cedicalcertificate": med_cert})
    # Access student's first name through the patient's user and linked student object
    student_first_name = patient.user.student.firstname if patient.user and hasattr(patient.user, 'student') and patient.user.student else 'N/A'
    messages.info(request, f"Issue Medical Certificate for {student_first_name.title()}")
    return render(request, "admin/med_cert.html", {"patient": patient})

# For uploading student from a csv file

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['file']
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            print(reader)
            for row in reader:
                print(row)
                Student.objects.create(
                    student_id=row['\ufeffstudID'],
                    lrn=row['lrn'],
                    lastname=row['lname'],
                    firstname=row['fname'],
                    middlename=row['mi'],
                    degree=row['degree'],
                    year_level=row['year_level'],
                    sex=row['sex'],
                    email=row['email_add'],
                    contact_number=row['contactnum']
                )
            messages.success(request, 'File uploaded and data imported successfully')
        # return redirect('medical: upload')
        return render(request, 'upload.html', {'form': form})
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})

@user_passes_test(is_admin)
def mental_health_view(request):
    student = None
    faculty = None
    patient = None
    user = None
    mental_health_record = None
    pending_count = MentalHealthRecord.objects.filter(status='pending').count()
    
    # Get search ID from either GET or POST request
    search_id = request.GET.get('search_id') or request.POST.get('search_id')
    
    # Fetch all student and faculty mental health records for the lists
    student_mhr_list = MentalHealthRecord.objects.filter(
        patient__isnull=False, 
        is_availing_mental_health=True
    ).select_related('patient__user')
    
    faculty_mhr_list = MentalHealthRecord.objects.filter(
        faculty__isnull=False, 
        is_availing_mental_health=True
    ).select_related('faculty__user')

    # If there's a search ID, fetch the single record for the Submitted Records section
    if search_id:
        fetched_mental_health_record = None # Initialize to None
        # Try to find a student first and get their associated mental health record
        try:
            student_obj = Student.objects.filter(student_id=search_id).first()
            if student_obj:
                patient_obj = Patient.objects.filter(user__email=student_obj.email).first()
                if patient_obj:
                    fetched_student = student_obj
                    fetched_patient = patient_obj
                    fetched_mental_health_record = MentalHealthRecord.objects.filter(patient=patient_obj).first()

            # If no mental health record found for a student, try to find a faculty and their associated mental health record
            if not fetched_mental_health_record:
                faculty_obj = Faculty.objects.filter(faculty_id=search_id).first()
                if faculty_obj:
                    fetched_faculty = faculty_obj
                    fetched_mental_health_record = MentalHealthRecord.objects.filter(faculty=faculty_obj).first()

            # Add a message if no record was found for the search ID
            if not fetched_mental_health_record:
                 messages.warning(request, f"No mental health record found for ID Number: {search_id}")

        except Exception as e:
            messages.error(request, f"Error fetching record for ID {search_id}: {e}")

    # Attach display details to mental health records lists
    for record in student_mhr_list:
        try:
            if record.patient and record.patient.user:
                student_obj = Student.objects.get(email=record.patient.user.email)
                record.id_number_display = student_obj.student_id
                record.name_display = f'{student_obj.firstname} {student_obj.lastname}'
            else:
                record.id_number_display = "N/A"
                record.name_display = "User/Patient Not Linked"
        except Student.DoesNotExist:
            record.id_number_display = "N/A"
            record.name_display = "Student Not Found"

    for record in faculty_mhr_list:
        try:
            if record.faculty and record.faculty.user:
                record.id_number_display = record.faculty.faculty_id
                record.name_display = record.faculty.user.get_full_name() or record.faculty.user.username
            else:
                record.id_number_display = "N/A"
                record.name_display = "User/Faculty Not Linked"
        except Exception as e:
            record.id_number_display = "Error"
            record.name_display = f"Error: {e}"

    # Handle POST requests for saving remarks or updating status
    if request.method == 'POST':
        record_id = request.POST.get('record_id')
        if record_id:
            try:
                mental_health_record = MentalHealthRecord.objects.get(pk=record_id)
                
                # Debugging: Check the fetched record and its links
                print(f"Fetched MentalHealthRecord PK: {mental_health_record.pk}")
                print(f"Linked Patient: {mental_health_record.patient}")
                print(f"Linked Faculty: {mental_health_record.faculty}")
                if mental_health_record.patient and mental_health_record.patient.user:
                    print(f"Patient's User: {mental_health_record.patient.user}")
                    print(f"Patient's User Email: {mental_health_record.patient.user.email}")
                elif mental_health_record.faculty and mental_health_record.faculty.user:
                    print(f"Faculty's User: {mental_health_record.faculty.user}")
                    print(f"Faculty's User Email: {mental_health_record.faculty.user.email}")
                else:
                    print("MentalHealthRecord is not linked to a Patient/Faculty with a User.")
                
                # Handle remarks update
                prescription_remarks = request.POST.get('prescription_remarks')
                certification_remarks = request.POST.get('certification_remarks')
                
                mhr_modified = False
                if prescription_remarks is not None and mental_health_record.prescription_remarks != prescription_remarks:
                    mental_health_record.prescription_remarks = prescription_remarks
                    mhr_modified = True
                if certification_remarks is not None and mental_health_record.certification_remarks != certification_remarks:
                    mental_health_record.certification_remarks = certification_remarks
                    mhr_modified = True
                
                # Handle status update
                status_action = request.POST.get('action')
                if status_action in ['approved', 'rejected'] and mental_health_record.status != status_action:
                    # Add debugging prints here
                    print(f"Processing status update for MentalHealthRecord PK: {mental_health_record.pk}")
                    print(f"Action: {status_action}")
                    print(f"Current Status: {mental_health_record.status}")

                    mental_health_record.status = status_action
                    mhr_modified = True
                    
                    # Create transaction record when mental health service is approved
                    if status_action == 'approved' and mental_health_record.is_availing_mental_health:
                        # Get the patient from either student or faculty
                        patient = None
                        if mental_health_record.patient:
                            patient = mental_health_record.patient
                        elif mental_health_record.faculty:
                            # Create a patient record for faculty if it doesn't exist
                            try:
                                patient = Patient.objects.get(user=mental_health_record.faculty.user)
                            except Patient.DoesNotExist:
                                patient = Patient.objects.create(
                                    user=mental_health_record.faculty.user,
                                    birth_date=None,  # Required field, set to None initially
                                    age=0,  # Required field, set to 0 initially
                                    weight=0,  # Required field, set to 0 initially
                                    height=0,  # Required field, set to 0 initially
                                    bloodtype='Unknown',  # Required field, set to default
                                    allergies='None',  # Required field, set to default
                                    medications='None',  # Required field, set to default
                                    home_address='',  # Required field, set to empty
                                    city='',  # Required field, set to empty
                                    state_province='',  # Required field, set to empty
                                    postal_zipcode='',  # Required field, set to empty
                                    country='',  # Required field, set to empty
                                    nationality='',  # Required field, set to empty
                                    religion='',  # Required field, set to empty
                                    civil_status='',  # Required field, set to empty
                                    number_of_children=0,  # Required field, set to 0
                                    academic_year='',  # Required field, set to empty
                                    section='',  # Required field, set to empty
                                    parent_guardian='',  # Required field, set to empty
                                    parent_guardian_contact_number=''  # Required field, set to empty
                                )
                        
                        if patient:
                            TransactionRecord.objects.create(
                                patient=patient,
                                transac_type="Mental Health Services",
                                transac_date=timezone.now()
                            )
                
                if mhr_modified:
                    mental_health_record.save()
                    messages.success(request, "Mental health record updated successfully.")

                    # Send email notification
                    user_for_email = None
                    if mental_health_record.patient and mental_health_record.patient.user:
                        user_for_email = mental_health_record.patient.user
                        print("User for email found via patient.")
                    elif mental_health_record.faculty and mental_health_record.faculty.user:
                        user_for_email = mental_health_record.faculty.user
                        print("User for email found via faculty.")
                        # Add more specific debugging prints for faculty
                        print(f"Faculty object: {mental_health_record.faculty}")
                        print(f"Faculty User object: {mental_health_record.faculty.user}")
                        if mental_health_record.faculty.user:
                            print(f"Faculty User email: {mental_health_record.faculty.user.email}")
                        else:
                             print("Faculty User is None.")
                    else:
                        print("User for email not found (neither patient nor faculty linked).")

                    if user_for_email and user_for_email.email:
                        recipient_email = user_for_email.email
                        recipient_name = user_for_email.get_full_name() or user_for_email.username

                        print(f"Attempting to send email to: {recipient_email}")

                        # Debugging: Print remark values before creating email content
                        print(f"Prescription Remarks: {mental_health_record.prescription_remarks}")
                        print(f"Certification Remarks: {mental_health_record.certification_remarks}")
                        print(f"Recipient Name: {recipient_name}")
                        print(f"Recipient Email: {recipient_email}")

                        # Initialize subject and html_message
                        subject = None
                        html_message = None

                        if mental_health_record.status == 'approved':
                            subject = 'Your Mental Health Record Has Been Approved'
                            template_name = 'email/mental_health_approved.html'
                        else:  # rejected
                            subject = 'Update Regarding Your Mental Health Record'
                            template_name = 'email/mental_health_rejected.html'

                        # Render email template
                        try:
                            html_message = render_to_string(template_name, {
                                'recipient_name': recipient_name,
                                'mental_health_record': mental_health_record,
                            })
                        except Exception as e:
                             print(f"Error rendering email template: {e}")
                             messages.error(request, f"Failed to render email content: {e}")
                             subject = None # Ensure subject is None if rendering fails
                             html_message = None # Ensure html_message is None if rendering fails

                        # Send email only if subject and html_message are defined
                        if subject and html_message:
                            print(f"Email subject: {subject}")
                            try:
                                send_mail(
                                    subject,
                                    '', # Empty plain text message
                                    settings.DEFAULT_FROM_EMAIL,
                                    [recipient_email],
                                    html_message=html_message,
                                    fail_silently=False,
                                )
                                print(f"Email notification sent successfully to {recipient_email}.")
                                messages.info(request, f"Email notification sent to {recipient_email}.")
                            except Exception as e:
                                print(f"Exception caught during email sending: {e}")
                                messages.error(request, f"Failed to send email notification: {e}")
                        else:
                             print("Subject or html_message not defined. Email not sent.")
                             messages.error(request, "Failed to prepare email content.")

                    else:
                         # More specific message when user or email is not found
                         print("Could not send email notification: User or User email not found for this record.")
                         messages.warning(request, "Could not send email notification: User or User email not found for this record.")

            except MentalHealthRecord.DoesNotExist:
                messages.error(request, "Mental health record not found.")
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")

        # Redirect to maintain search context if there was a search
        if search_id:
            return redirect(f'{request.path}?search_id={search_id}')
        return redirect(request.path)

    # --- Fetch the single record for the Submitted Records section based on search_id ---
    fetched_student = None
    fetched_faculty = None
    fetched_patient = None
    fetched_mental_health_record = None

    if search_id:
        try:
            # Try to find a student first and get their associated patient
            student_obj = Student.objects.filter(student_id=search_id).first()
            if student_obj:
                patient_obj = Patient.objects.filter(user__email=student_obj.email).first()
                if patient_obj:
                    fetched_student = student_obj
                    fetched_patient = patient_obj
                    # Fetch the mental health record using the patient object
                    fetched_mental_health_record = MentalHealthRecord.objects.filter(patient=patient_obj).first()

            # If not found as a student, try to find a faculty and their associated mental health record
            if not fetched_mental_health_record:
                faculty_obj = Faculty.objects.filter(faculty_id=search_id).first()
                if faculty_obj:
                    fetched_faculty = faculty_obj
                    # Fetch the mental health record using the faculty object
                    fetched_mental_health_record = MentalHealthRecord.objects.filter(faculty=faculty_obj).first()

            # If a search ID was provided but no record was found (handled in template)
            # messages.warning(request, f"No record found for ID Number: {search_id}")

        except Exception as e:
            # Handle potential errors during fetching
            messages.error(request, f"Error fetching record for ID {search_id}: {e}")

    context = {
        'student_mhr_list': student_mhr_list,
        'faculty_mhr_list': faculty_mhr_list,
        'pending_count': pending_count,
        'search_id': search_id,
        'fetched_student': fetched_student,
        'fetched_faculty': fetched_faculty,
        'fetched_patient': fetched_patient, # Although not strictly needed in template now, keep for completeness
        'fetched_mental_health_record': fetched_mental_health_record,
    }

    return render(request, 'admin/mental_health.html', context)

@user_passes_test(is_admin)
def update_mental_health_status(request, pk):
    """
    View to update the status of a mental health record.
    This is typically called via AJAX from the mental health list view.
    """
    if request.method == 'POST':
        try:
            # Get the mental health record
            mental_health_record = MentalHealthRecord.objects.get(pk=pk)
            
            # Get the new status from POST data
            new_status = request.POST.get('status')
            if new_status not in ['pending', 'approved', 'rejected']:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid status value'
                }, status=400)
            
            # Update the status
            mental_health_record.status = new_status
            mental_health_record.save()
            
            # Get user for email notification
            user_for_email = None
            if mental_health_record.patient and mental_health_record.patient.user:
                user_for_email = mental_health_record.patient.user
            elif mental_health_record.faculty and mental_health_record.faculty.user:
                user_for_email = mental_health_record.faculty.user
            
            # Send email notification if we have a valid user
            if user_for_email and user_for_email.email:
                recipient_email = user_for_email.email
                recipient_name = user_for_email.get_full_name() or user_for_email.username
                
                # Prepare email content based on status
                if new_status == 'approved':
                    subject = 'Your Mental Health Record Has Been Approved'
                    template_name = 'email/mental_health_approved.html'
                else:  # rejected
                    subject = 'Update Regarding Your Mental Health Record'
                    template_name = 'email/mental_health_rejected.html'
                
                # Render email template
                html_message = render_to_string(template_name, {
                    'recipient_name': recipient_name,
                    'mental_health_record': mental_health_record,
                })
                
                try:
                    send_mail(
                        subject,
                        '',  # Empty plain text message
                        settings.DEFAULT_FROM_EMAIL,
                        [recipient_email],
                        html_message=html_message,
                        fail_silently=False,
                    )
                except Exception as e:
                    # Log the email error but don't fail the request
                    print(f"Failed to send email notification: {e}")
            
            return JsonResponse({
                'success': True,
                'status': new_status,
                'message': f'Status updated to {new_status}'
            })
            
        except MentalHealthRecord.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Mental health record not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Method not allowed'
    }, status=405)

@login_required
def update_mental_health_choice(request):
    if request.method == 'POST':
        is_availing = request.POST.get('avail_mental_health') == 'yes'
        
        user = request.user
        mental_health_record = None

        student = get_student_by_user(user)
        faculty = get_faculty_by_user(user)

        if student:
            # If the user is a student, get their associated patient record
            patient = get_object_or_404(Patient, user=user)
            mental_health_record, created = MentalHealthRecord.objects.get_or_create(patient=patient)
        elif faculty:
            # If the user is a faculty, directly use the faculty object
            mental_health_record, created = MentalHealthRecord.objects.get_or_create(faculty=faculty)
        else:
            return JsonResponse({'error': 'User is neither student nor faculty.'}, status=400)

        mental_health_record.is_availing_mental_health = is_availing
        mental_health_record.save()

        return JsonResponse({'message': 'Mental health choice updated successfully.'}, status=200)
    return JsonResponse({'error': 'Invalid request method.'}, status=405)
