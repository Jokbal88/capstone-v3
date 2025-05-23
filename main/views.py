from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from main.models import Student, EmailVerification
from medical.models import (
    PhysicalExamination,
    Patient,
    MedicalHistory,
    FamilyMedicalHistory,
    RiskAssessment,
    MentalHealthRecord,
    PatientRequest,
    TransactionRecord,
    DentalRecords,
    PrescriptionRecord
)
from datetime import datetime, date
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from medical import models as medical_models
from django.http import JsonResponse
from .utils import send_verification_email, send_password_reset_email
import uuid
from django.utils.crypto import get_random_string
from django.contrib.messages import get_messages
from django.views.decorators.csrf import ensure_csrf_cookie
import re

def is_admin(user):
    return user.is_staff

@ensure_csrf_cookie
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('email')
        password = request.POST.get('password')
        next_url = request.POST.get('next', '')

        user = authenticate(request, username=username, password=password)
        
        if user is None:
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is not None:
            # Check if email is verified
            try:
                verification = EmailVerification.objects.get(user=user)
                if not verification.is_verified:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Please verify your email address before logging in.'
                    })
            except EmailVerification.DoesNotExist:
                # Create verification if it doesn't exist
                verification = EmailVerification.objects.create(user=user)
                send_verification_email(user, verification)
                return JsonResponse({
                    'status': 'error',
                    'message': 'Please verify your email address before logging in. A new verification email has been sent.'
                })

            login(request, user)
            
            # --- Handle Welcome Message for First Login --- #
            # Check if this is the user's first login
            if not request.session.get('_has_logged_in_before', False):
                messages.success(request, 'Welcome to HealthHub Connect!')
                request.session['_has_logged_in_before'] = True # Set the flag
            else:
                # If not the first login, show a 'Welcome!' message
                messages.info(request, 'Welcome!')
            # --- End of Welcome Message Logic ---
            
            # Handle admin login
            if next_url and (user.is_staff or user.is_superuser):
                return redirect(next_url)
            
            # Redirect based on user type
            if user.is_staff or user.is_superuser:
                redirect_url = 'main:admin_dashboard'
            else:
                redirect_url = 'main:student_dashboard'
            
            return JsonResponse({
                'status': 'success',
                'redirect_url': reverse(redirect_url)
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid ID number/Email or password'
            })

    # Get messages and convert them to a list of dictionaries
    messages_list = []
    for message in get_messages(request):
        messages_list.append({
            'message': message.message,
            'tags': message.tags
        })

    return render(request, 'login.html', {
        'messages': messages_list,
        'next': request.GET.get('next', '')
    })

def register(request):
    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.POST.get('firstName')
            middle_initial = request.POST.get('middleInitial')
            last_name = request.POST.get('lastName')
            sex = request.POST.get('sex')
            year_level = request.POST.get('yrLevel')
            student_id = request.POST.get('idNumber')
            lrn = request.POST.get('lrn')
            degree = request.POST.get('course')
            email = request.POST.get('email')
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirmPassword')

            # --- Validation Errors --- #
            general_errors = []
            password_errors = []

            # Check if passwords match
            if password != confirm_password:
                password_errors.append('Passwords do not match.')

            # Check password length (server-side)
            if len(password) < 8:
                password_errors.append('Password must be at least 8 characters long.')

            # Check for complexity (using regex)
            if not re.search(r'[A-Z]', password):
                password_errors.append('Password must contain at least one uppercase letter.')
            if not re.search(r'[a-z]', password):
                password_errors.append('Password must contain at least one lowercase letter.')
            if not re.search(r'\d', password):
                password_errors.append('Password must contain at least one digit.')
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                password_errors.append('Password must contain at least one symbol (!@#$%^&*(),.?":{}|<>).')

            # Check if student ID or email already exists
            if User.objects.filter(username=student_id).exists():
                general_errors.append(f'Student ID {student_id} is already registered.')
            if User.objects.filter(email=email).exists():
                general_errors.append(f'Email {email} is already registered.')

            # If there are any errors (password or general), return with errors
            if general_errors or password_errors:
                # Add general errors to Django messages (for SweetAlert)
                for error in general_errors:
                    messages.error(request, error)
                # Return password errors in context for inline display
                return render(request, 'register.html', {
                    'password_errors': password_errors,
                    'form_data': request.POST # Pass POST data back to repopulate form
                })

            # --- If validation passes, proceed with creation --- #
            print("Validation passed. Attempting to create user and student.") # Debug log

            # Create User account
            user = User.objects.create_user(
                username=student_id,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            print(f"User account created for username: {user.username}") # Debug log

            # Create Student in main app only
            student = Student.objects.create(
                student_id=student_id,
                lrn=lrn,
                lastname=last_name,
                firstname=first_name,
                middlename=middle_initial,
                degree=degree,
                year_level=int(year_level),
                sex=sex,
                email=email,
                contact_number=''
            )

            # Create email verification
            verification = EmailVerification.objects.create(user=user)
            
            # Send verification email
            send_verification_email(user, verification)
            print("Verification email sent.") # Debug log

            messages.success(request, 'Registration successful! Please check your email to verify your account.')
            print("Registration successful, redirecting to login.") # Debug log
            return redirect('main:login')

        except Exception as e:
            # Catch any other unexpected errors
            print(f"An unexpected error occurred during registration: {e}") # Debug log: print the specific error
            messages.error(request, f'An unexpected error occurred during registration: {str(e)}')
            return render(request, 'register.html', request.POST) # Render with POST data

    # For GET request, render the empty form
    return render(request, 'register.html')

def verify_email(request, token):
    try:
        verification = EmailVerification.objects.get(token=token)
        
        if verification.is_token_expired():
            messages.error(request, 'Verification link has expired. Please request a new one.')
            return redirect('main:login')
        
        verification.is_verified = True
        verification.save()
        
        messages.success(request, 'Email verified successfully! You can now log in.')
        return redirect('main:login')
        
    except EmailVerification.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('main:login')

def resend_verification(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            verification, created = EmailVerification.objects.get_or_create(user=user)
            
            if not created and verification.is_verified:
                messages.info(request, 'Email is already verified.')
                return redirect('main:login')
            
            # Update token and timestamp
            verification.token = uuid.uuid4()
            verification.created_at = timezone.now()
            verification.save()
            
            # Send new verification email
            send_verification_email(user, verification)
            
            messages.success(request, 'A new verification email has been sent.')
            return redirect('main:login')
            
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
            return redirect('main:login')
    
    return render(request, 'resend_verification.html')

def recovery(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            # Generate a unique token
            token = str(uuid.uuid4())
            # Store the token in the session
            request.session['reset_token'] = token
            request.session['reset_email'] = email
            
            # Send password reset email
            send_password_reset_email(user, token)
            
            # Return JSON response for success
            return JsonResponse({
                'status': 'success',
                'message': 'Password reset instructions have been sent to your email.'
            })
            
        except User.DoesNotExist:
            # Return JSON response for error (user not found)
            return JsonResponse({
                'status': 'error',
                'message': 'No account found with this email address.'
            })
        except Exception as e:
             # Return JSON response for other errors
            return JsonResponse({
                'status': 'error',
                'message': f'An error occurred: {str(e)}'
            })
            
    return render(request, 'recovery.html')

def password_reset(request, token):
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'password-reset.html', {'token': token})
            
        try:
            # Find the user with this token in their session
            for user in User.objects.all():
                if request.session.get('reset_token') == token and request.session.get('reset_email') == user.email:
                    user.set_password(new_password)
                    user.save()
                    
                    # Clear the session
                    del request.session['reset_token']
                    del request.session['reset_email']
                    
                    messages.success(request, 'Your password has been reset successfully.')
                    return redirect('main:login')
            
            messages.error(request, 'Invalid or expired reset link.')
            return redirect('main:recovery')
            
        except Exception as e:
            messages.error(request, 'An error occurred while resetting your password.')
            return redirect('main:recovery')
            
    return render(request, 'password-reset.html', {'token': token})


@login_required
def main_view(request):
    if request.user.is_authenticated:
        # For regular users (students)
        if not request.user.is_staff and not request.user.is_superuser:
            try:
                # Check medical student record
                medical_student = medical_models.Student.objects.get(student_id=request.user.username)
                
                # Check if student has completed medical profile
                try:
                    patient = medical_models.Patient.objects.get(student=medical_student)
                    # If patient record exists, show main dashboard
                    return render(request, 'mainv2.html', {'student': medical_student})
                except medical_models.Patient.DoesNotExist:
                    # If no patient record, redirect to patient form
                    messages.info(request, 'Please complete your medical profile first.')
                    return redirect('main:patient_form')
                    
            except medical_models.Student.DoesNotExist:
                messages.error(request, 'Student profile not found.')
                return redirect('main:login')
        # For staff/admin users
        else:
            return render(request, 'mainv2.html')
    return redirect('main:login')

@login_required
def patient_form(request):
    if request.method == 'GET':
        try:
            patient = medical_models.Patient.objects.get(student_id=request.user.username)
            return redirect('main:dashboard')
        except medical_models.Patient.DoesNotExist:
            pass
    if request.method == 'POST':
        try:
            # Get the medical student instance
            medical_student = medical_models.Student.objects.get(student_id=request.user.username)
            
            # Create PhysicalExamination first
            physical_exam = medical_models.PhysicalExamination.objects.create(
                student=medical_student,
                date_of_physical_examination=timezone.now().strftime('%Y-%m-%d')
            )
            
            # Create Patient record
            patient = medical_models.Patient.objects.create(
                student=medical_student,
                birth_date=request.POST.get('birth_date'),
                age=calculate_age(request.POST.get('birth_date')),
                weight=float(request.POST.get('weight')),
                height=float(request.POST.get('height')),
                bloodtype=request.POST.get('bloodtype'),
                allergies=process_checkboxes(request.POST.getlist('allergies'), request.POST.get('other_allergies')),
                medications=request.POST.get('medications', 'None'),
                home_address=request.POST.get('home_address'),
                city=request.POST.get('city'),
                state_province=request.POST.get('state_province'),
                postal_zipcode=request.POST.get('postal_zipcode'),
                country=request.POST.get('country'),
                nationality=request.POST.get('nationality'),
                civil_status=request.POST.get('civil_status'),
                number_of_children=0,
                academic_year=f"{timezone.now().year}-{timezone.now().year + 1}",
                section=request.POST.get('section', 'TBA'),
                parent_guardian=request.POST.get('parent_guardian'),
                parent_guardian_contact_number=request.POST.get('parent_guardian_contact'),
                examination=physical_exam
            )
            
            # --- Medical History logic ---
            med_hist_list = request.POST.getlist('medical_history')
            if 'No Medical History' in med_hist_list:
                med_hist_list = ['No Medical History']
            # --- Family Medical History logic ---
            fam_hist_list = request.POST.getlist('family_history')
            if 'No Family History' in fam_hist_list:
                fam_hist_list = ['No Family History']
            # --- Risk Assessment logic ---
            risk_list = request.POST.getlist('risk_assessment')
            if 'No Risk' in risk_list:
                risk_list = ['No Risk']

            # Create MedicalHistory record
            medical_history = medical_models.MedicalHistory.objects.create(
                examination=physical_exam,
                tuberculosis='tuberculosis' in med_hist_list,
                hypertension='hypertension' in med_hist_list,
                heart_disease='heart_disease' in med_hist_list,
                hernia='hernia' in med_hist_list,
                epilepsy='epilepsy' in med_hist_list,
                peptic_ulcer='peptic_ulcer' in med_hist_list,
                kidney_disease='kidney_disease' in med_hist_list,
                asthma='asthma' in med_hist_list,
                insomnia='insomnia' in med_hist_list,
                malaria='malaria' in med_hist_list,
                venereal_disease='venereal_disease' in med_hist_list,
                nervous_breakdown='nervous_breakdown' in med_hist_list,
                jaundice='jaundice' in med_hist_list,
                others=request.POST.get('other_medical', ''),
                no_history='No Medical History' in med_hist_list
            )
            
            # Create FamilyMedicalHistory record
            family_history = medical_models.FamilyMedicalHistory.objects.create(
                examination=physical_exam,
                hypertension='hypertension' in fam_hist_list,
                asthma='asthma' in fam_hist_list,
                cancer='cancer' in fam_hist_list,
                tuberculosis='tuberculosis' in fam_hist_list,
                diabetes='diabetes' in fam_hist_list,
                bleeding_disorder='bleeding_disorder' in fam_hist_list,
                epilepsy='epilepsy' in fam_hist_list,
                mental_disorder='mental_disorder' in fam_hist_list,
                no_history='No Family History' in fam_hist_list,
                other_medical_history=request.POST.get('other_family_medical', '')
            )
            
            # Create RiskAssessment record
            risk_assessment = medical_models.RiskAssessment.objects.create(
                clearance=patient,
                cardiovascular_disease='cardiovascular' in risk_list,
                chronic_lung_disease='chronic_lung' in risk_list,
                chronic_renal_disease='chronic_kidney' in risk_list,
                chronic_liver_disease='chronic_liver' in risk_list,
                cancer='cancer' in risk_list,
                autoimmune_disease='autoimmune' in risk_list,
                pwd='pwd' in risk_list,
                disability=request.POST.get('disability', '')
            )
            
            messages.success(request, 'Medical information submitted successfully!')
            return redirect('main:student_dashboard')
            
        except medical_models.Student.DoesNotExist:
            messages.error(request, 'Student profile not found.')
            return redirect('main:login')
        except Exception as e:
            print(e)
            messages.error(request, f'Error saving patient information: {str(e)}')
            return render(request, 'patient_form.html')
        
    # For GET request or POST with errors, render the form with current date
    today = date.today()
    context = {
        'current_date': today
    }
    return render(request, 'patient_form.html', context)

def calculate_age(birthdate):
    born = datetime.strptime(birthdate, '%Y-%m-%d').date()
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

def process_checkboxes(checkbox_list, other_value):
    if 'None' in checkbox_list:
        return 'None'
    result = ', '.join(filter(None, checkbox_list))
    if other_value:
        result = f"{result}, {other_value}" if result else other_value
    return result or 'None'

@user_passes_test(is_admin)
def admin_dashboard_view(request):
    # Get total patients count
    total_patients = Patient.objects.count()
    
    # Get total medical records
    total_records = PhysicalExamination.objects.count()
    
    # Get pending requests (not approved)
    pending_requests = PatientRequest.objects.filter(approve=False).count()
    
    # Get today's schedule count
    today = timezone.now().date()
    todays_schedule = PatientRequest.objects.filter(
        date_requested__date=today,
        approve=True
    ).count()
    
    # Get all requests with patient and student information
    upcoming_requests = PatientRequest.objects.select_related(
        'patient',
        'patient__student'
    ).order_by('date_requested')
    
    # Get dental service requests
    dental_requests = DentalRecords.objects.select_related(
        'patient',
        'patient__student'
    ).filter(appointed=False).order_by('date_requested')
    
    # DEBUG: Print dental requests
    print('--- Dental Requests ---')
    for req in dental_requests:
        print(f'{req.date_requested} - {req.service_type} - {req.patient.student.firstname}')
    print('--- End of Dental Requests ---')
    
    # Get scheduled appointments for the calendar (include all requests, not just future)
    scheduled_appointments = PatientRequest.objects.select_related(
        'patient',
        'patient__student'
    ).values(
        'date_requested',
        'approve',
        'patient__student__firstname',
        'patient__student__lastname',
        'request_type'
    )
    
    # Format appointments for the calendar
    events = []
    for appointment in scheduled_appointments:
        events.append({
            'date': appointment['date_requested'].strftime('%Y-%m-%d'),
            'student': f"{appointment['patient__student__firstname']} {appointment['patient__student__lastname']}",
            'service': appointment['request_type'],
            'status': 'approved' if appointment['approve'] else 'pending'
        })
    
    # Example: Urgent cases (patients with allergies or chronic conditions)
    urgent_cases = Patient.objects.filter(allergies__isnull=False).count()
    
    # Emergency Assistance Requests (example: filter by request_type containing 'Emergency')
    emergency_requests = PatientRequest.objects.select_related(
        'patient',
        'patient__student'
    ).filter(request_type__icontains='emergency').order_by('date_requested')
    
    # Mental Health Requests (pending or recently submitted)
    mental_health_requests = MentalHealthRecord.objects.select_related(
        'patient',
        'patient__student'
    ).order_by('-date_submitted')
    
    # Get prescription requests
    prescription_requests = PrescriptionRecord.objects.select_related(
        'patient',
        'patient__student'
    ).order_by('-date_prescribed')
    
    # Notifications (sample)
    notifications = []
    if pending_requests > 0:
        notifications.append(f"{pending_requests} new documentary requests pending approval.")
    if urgent_cases > 0:
        notifications.append(f"{urgent_cases} urgent cases require attention.")
    if emergency_requests.count() > 0:
        notifications.append(f"{emergency_requests.count()} emergency assistance requests pending.")
    
    # Today's Appointments
    today_str = timezone.now().strftime('%Y-%m-%d')
    todays_appointments = []
    for event in events:
        if event['date'] == today_str:
            # If you have time info, add it here; else, use a placeholder
            appt_time = event.get('time', 'All Day')
            todays_appointments.append({
                'student': event['student'],
                'service': event['service'],
                'time': appt_time
            })
    
    context = {
        'total_patients': total_patients,
        'total_records': total_records,
        'pending_requests': pending_requests,
        'todays_schedule': todays_schedule,
        'urgent_cases': urgent_cases,
        'upcoming_requests': upcoming_requests,
        'dental_requests': dental_requests,
        'emergency_requests': emergency_requests,
        'mental_health_requests': mental_health_requests,
        'prescription_requests': prescription_requests,
        'events': events,
        'notifications': notifications,
        'todays_appointments': todays_appointments,
    }
    
    return render(request, 'admin_dashboard.html', context)

@login_required
def dashboard_view(request):
    try:
        # Get student by student_id (username)
        student = Student.objects.get(student_id=request.user.username)
        
        try:
            # Get the medical student instance
            medical_student = medical_models.Student.objects.get(student_id=student.student_id)
            
            # Get patient record and related data
            patient = medical_models.Patient.objects.get(student=medical_student)
            physical_exam = patient.examination
            medical_history = medical_models.MedicalHistory.objects.get(examination=physical_exam)
            family_history = medical_models.FamilyMedicalHistory.objects.get(examination=physical_exam)
            risk_assessment = medical_models.RiskAssessment.objects.get(clearance=patient)
            # Get patient requests
            patient_requests = PatientRequest.objects.filter(patient=patient).order_by('-date_requested')
            
            context = {
                'student': student,
                'patient': patient,
                'medical_history': medical_history,
                'family_history': family_history,
                'risk_assessment': risk_assessment,
                'physical_exam': physical_exam,
                'patient_requests': patient_requests,
            }
            
            return render(request, 'student_dashboard.html', context)
            
        except medical_models.Student.DoesNotExist:
            messages.error(request, 'Medical student profile not found.')
            return redirect('main:login')
        except medical_models.Patient.DoesNotExist:
            messages.info(request, 'Please complete your medical profile first.')
            return redirect('main:patient_form')
        except Exception as e:
            print(e)
            messages.error(request, 'Error loading dashboard data.')
            return redirect('main:login')
            
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('main:login')
    except Exception as e:
        print(e)
        messages.error(request, 'An error occurred.')
        return redirect('main:login')

@user_passes_test(is_admin)
def mental_health_view(request):
    records = MentalHealthRecord.objects.all().order_by('-date_submitted')
    pending_count = records.filter(status='pending').count()
    
    context = {
        'records': records,
        'pending_count': pending_count,
    }
    return render(request, 'admin/mental_health.html', context)

@login_required
def mental_health_submit(request):
    if request.method == 'POST':
        try:
            patient = Patient.objects.get(student__student_id=request.user.username)
            prescription = request.FILES.get('prescription')
            certification = request.FILES.get('certification')
            
            if not prescription or not certification:
                messages.error(request, 'Both prescription and certification are required.')
                return redirect('main:mental_health')
            
            MentalHealthRecord.objects.create(
                patient=patient,
                prescription=prescription,
                certification=certification
            )
            
            messages.success(request, 'Mental health documents submitted successfully.')
            return redirect('main:student_dashboard')
            
        except Patient.DoesNotExist:
            messages.error(request, 'Patient profile not found.')
            return redirect('main:patient_form')
            
    return render(request, 'mental_health_submit.html')

@user_passes_test(is_admin)
def mental_health_review(request, record_id):
    record = get_object_or_404(MentalHealthRecord, id=record_id)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        notes = request.POST.get('notes')
        
        record.status = status
        record.notes = notes
        record.reviewed_by = request.user
        record.reviewed_at = timezone.now()
        record.save()
        
        # Send email notification to student
        subject = f'Mental Health Record Review - {status.title()}'
        message = f"""
        Dear {record.patient.student.firstname},
        
        Your mental health records have been reviewed.
        Status: {status.title()}
        
        Notes: {notes if notes else 'No additional notes.'}
        
        Best regards,
        Medical Services Team
        """
        
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [record.patient.student.email],
            fail_silently=False,
        )
        
        messages.success(request, 'Record reviewed successfully.')
        return redirect('main:mental_health')
        
    return render(request, 'admin/mental_health_review.html', {'record': record})

def logout_view(request):
    logout(request)
    return redirect('main:login')

def email_verification(request):
    return render(request, 'email_verification.html')

@login_required
def upload_profile_picture_view(request):
    if request.method == 'POST':
        # Ensure a file was uploaded
        if 'profile_picture' in request.FILES:
            uploaded_file = request.FILES['profile_picture']
            user = request.user
            
            try:
                # Get the patient instance for the logged-in user
                # Assuming Student.student_id matches User.username
                student = medical_models.Student.objects.get(student_id=user.username)
                patient = medical_models.Patient.objects.get(student=student)
                
                # Save the uploaded file to the profile_picture field
                patient.profile_picture = uploaded_file
                patient.save()
                messages.success(request, 'Profile picture uploaded successfully!')
                
            except medical_models.Student.DoesNotExist:
                messages.error(request, 'Student profile not found.')
            except medical_models.Patient.DoesNotExist:
                messages.error(request, 'Patient profile not found.')
            except Exception as e:
                messages.error(request, f'Error uploading profile picture: {e}')
                
        else:
            messages.error(request, 'No file was uploaded.')
            
        # Redirect back to the student dashboard
        return redirect('main:student_dashboard')
    else:
        # Handle GET requests if necessary, or return an error
        messages.error(request, 'Invalid request method.')
        return redirect('main:student_dashboard')