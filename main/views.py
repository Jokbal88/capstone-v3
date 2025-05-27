from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from main.models import Student, EmailVerification, Profile
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
import random
from django.views.decorators.http import require_http_methods

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
            # Always generate and send OTP for login
            try:
                verification = EmailVerification.objects.get(user=user)
            except EmailVerification.DoesNotExist:
                verification = EmailVerification.objects.create(user=user)
            
            # Generate new OTP
            otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            verification.otp = otp
            verification.created_at = timezone.now()
            verification.save()
            
            # Send verification email
            send_verification_email(user, verification)
            
            # Store email in session for OTP verification
            request.session['verification_email'] = user.email
            
            return JsonResponse({
                'status': 'success',
                'message': 'OTP sent to your email',
                'show_otp': True
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

@require_http_methods(["GET", "POST"])
def register(request):
    if request.method == "POST":
        try:
            # Get form data
            firstName = request.POST.get("firstName")
            middleInitial = request.POST.get("middleInitial")
            lastName = request.POST.get("lastName")
            sex = request.POST.get("sex")
            yrLevel = request.POST.get("yrLevel")
            idNumber = request.POST.get("idNumber")
            lrn = request.POST.get("lrn")
            course = request.POST.get("course")
            email = request.POST.get("email")
            password = request.POST.get("password")
            confirmPassword = request.POST.get("confirmPassword")
            role = request.POST.get("role", 'Student') # Get selected role, default to Student

            # Validate LRN format only for students
            if role == 'Student':
                if not lrn or not lrn.isdigit() or len(lrn) != 12:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'LRN must be exactly 12 digits.'
                    })

                # Validate ID Number format only for students
                if not idNumber or not idNumber.isdigit() or len(idNumber) != 7:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'ID Number must be exactly 7 digits.'
                    })


            # Check if email already exists
            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Email already registered.'
                })

            # Check if student ID already exists (only for students)
            if role == 'Student' and Student.objects.filter(student_id=idNumber).exists():
                 return JsonResponse({
                     'status': 'error',
                     'message': 'Student ID already registered.'
                 })

            # Check if LRN already exists (only for students)
            if role == 'Student' and Student.objects.filter(lrn=lrn).exists():
                 return JsonResponse({
                     'status': 'error',
                     'message': 'LRN already registered.'
                 })

            # Validate password
            if password != confirmPassword:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Passwords do not match.'
                })

            # Create user
            user = User.objects.create_user(
                username=email, # Using email as username
                email=email,
                password=password,
                first_name=firstName, # Use Django's built-in fields
                last_name=lastName,
            )

            # Create Profile for the user
            profile = Profile.objects.create(user=user, role=role)

            # Create Student instance only if the role is Student
            if role == 'Student':
                 # Further validate required fields for students
                 if not all([sex, yrLevel, course]):
                      return JsonResponse({
                           'status': 'error',
                           'message': 'Please provide all required student information.'
                      })

                 Student.objects.create(
                     student_id=idNumber,
                     lrn=lrn,
                     lastname=lastName,
                     firstname=firstName,
                     middlename=middleInitial,
                     degree=course,
                     year_level=int(yrLevel), # Convert to integer
                     sex=sex,
                     email=email,
                     contact_number='N/A' # Assuming contact number is not collected in this form
                 )

            # Generate OTP and create verification
            otp = ''.join(random.choices('0123456789', k=6))
            verification = EmailVerification.objects.create(user=user, otp=otp)
            
            # Send verification email
            send_verification_email(user, verification)

            return JsonResponse({
                'status': 'success',
                'message': 'Registration successful. Please check your email for the verification code.'
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })

    return render(request, "register.html")

def verify_otp(request):
    if request.method == 'POST':
        email = request.session.get('verification_email')
        otp = request.POST.get('otp')
        
        print(f"Received OTP for email: {email}")
        print(f"Entered OTP: {otp}")

        if not email:
            return JsonResponse({
                'status': 'error',
                'message': 'No verification session found. Please try logging in again.'
            })
        
        try:
            user = User.objects.get(email=email)
            verification = EmailVerification.objects.get(user=user)
            
            if verification.is_otp_expired():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Verification code has expired. Please request a new one.'
                })
            
            if verification.otp == otp:
                print("OTP matched!")
                verification.is_verified = True
                verification.save()
                
                # Log the user in
                login(request, user)
                
                # Clear the verification session
                del request.session['verification_email']
                
                # Return success response with appropriate redirect URL
                if user.is_staff or user.is_superuser:
                    return JsonResponse({
                        'status': 'success',
                        'redirect_url': reverse('main:admin_dashboard')
                    })
                else:
                    return JsonResponse({
                        'status': 'success',
                        'redirect_url': reverse('main:student_dashboard')
                    })
            else:
                print(f"OTP mismatch. Stored OTP: {verification.otp}")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid verification code.'
                })
                
        except (User.DoesNotExist, EmailVerification.DoesNotExist):
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid email address.'
            })
    
    # For GET requests, get email from session
    email = request.session.get('verification_email')
    if not email:
        messages.error(request, 'No verification session found. Please try logging in again.')
        return redirect('main:login')
    
    return render(request, 'verify_otp.html', {'email': email})

def resend_verification(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            verification, created = EmailVerification.objects.get_or_create(user=user)
            
            if not created and verification.is_verified:
                messages.info(request, 'Email is already verified.')
                return redirect('main:login')
            
            # Generate new OTP
            otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            # Update OTP and timestamp
            verification.otp = otp
            verification.created_at = timezone.now()
            verification.save()
            
            # Send new verification email
            send_verification_email(user, verification)
            
            messages.success(request, 'A new verification code has been sent.')
            return redirect('main:verify_otp')
            
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
    # First check if the session has the required data
    if not request.session.get('reset_token') or not request.session.get('reset_email'):
        return JsonResponse({
            'status': 'error',
            'message': 'Your password reset session has expired. Please request a new password reset link.'
        })

    if request.method == 'POST':
        try:
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if not new_password or not confirm_password:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Both password fields are required.'
                })
            
            # Password validation
            password_errors = []
            
            # Check password length
            if len(new_password) < 8:
                password_errors.append('Password must be at least 8 characters long.')
            
            # Check for uppercase letter
            if not re.search(r'[A-Z]', new_password):
                password_errors.append('Password must contain at least one uppercase letter.')
            
            # Check for lowercase letter
            if not re.search(r'[a-z]', new_password):
                password_errors.append('Password must contain at least one lowercase letter.')
            
            # Check for digit
            if not re.search(r'\d', new_password):
                password_errors.append('Password must contain at least one number.')
            
            # Check for special character
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password):
                password_errors.append('Password must contain at least one special character (!@#$%^&*(),.?":{}|<>).')
            
            # If there are password validation errors, return them
            if password_errors:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Password validation failed:',
                    'errors': password_errors
                })
            
            if new_password != confirm_password:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Passwords do not match.'
                })
            
            # Verify the token matches
            if request.session.get('reset_token') != token:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid or expired reset link. Please request a new password reset.'
                })

            # Get the email from session
            reset_email = request.session.get('reset_email')
            
            # Find the user with this email
            try:
                user = User.objects.get(email=reset_email)
            except User.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'User not found. Please request a new password reset.'
                })

            # Update the password
            user.set_password(new_password)
            user.save()
            
            # Clear the session
            del request.session['reset_token']
            del request.session['reset_email']
            
            # Return success response
            return JsonResponse({
                'status': 'success',
                'message': 'Your password has been reset successfully! You can now log in with your new password.',
                'redirect_url': reverse('main:login')
            })
        
        except Exception as e:
            print(f"Password reset error: {str(e)}")  # For debugging
            return JsonResponse({
                'status': 'error',
                'message': 'An error occurred while resetting your password. Please try again.'
            })
    
    # For GET requests, render the form
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
            
            record = MentalHealthRecord.objects.create(
                patient=patient,
                prescription=prescription,
                certification=certification
            )
            
            # Send notification email to student
            subject = 'Mental Health Record Submission Confirmation'
            message = f"""
            Dear {patient.student.firstname},

            This email confirms that we have received your mental health record submission.

            Submission Details:
            - Date Submitted: {record.date_submitted.strftime('%B %d, %Y')}
            - Status: Pending Review

            Our medical team will review your submission and you will be notified of the outcome.

            Best regards,
            Medical Services Team
            """
            
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [patient.student.email],
                fail_silently=False,
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
        status = request.POST.get('status', '').lower()
        notes = request.POST.get('notes', '')
        prescription_remarks = request.POST.get('prescription_remarks', '')
        certification_remarks = request.POST.get('certification_remarks', '')
        
        # Validate status
        valid_statuses = ['approved', 'rejected', 'pending']
        if status not in valid_statuses:
            messages.error(request, f'Invalid status provided. Must be one of: {", ".join(valid_statuses)}')
            return redirect('main:mental_health')
        
        # Update record
        record.status = status
        record.notes = notes
        record.prescription_remarks = prescription_remarks
        record.certification_remarks = certification_remarks
        record.reviewed_by = request.user
        record.reviewed_at = timezone.now()
        record.save()
        
        # Initialize email variables
        subject = ''
        message = ''
        
        # Prepare email content based on status
        if status == 'approved':
            subject = 'Mental Health Record - Approved'
            message = f"""
            Dear {record.patient.student.firstname},

            We are pleased to inform you that your mental health record has been approved.

            Review Details:
            - Date Reviewed: {record.reviewed_at.strftime('%B %d, %Y')}
            - Status: Approved
            - Reviewer: {record.reviewed_by.get_full_name()}

            Document Review:
            - Prescription Document: {prescription_remarks if prescription_remarks else 'Approved'}
            - Certification Document: {certification_remarks if certification_remarks else 'Approved'}

            Additional Notes:
            {notes if notes else 'No additional notes provided.'}

            Your mental health record is now complete and on file.

            Best regards,
            Medical Services Team
            """
        elif status == 'rejected':
            subject = 'Mental Health Record - Additional Information Required'
            message = f"""
            Dear {record.patient.student.firstname},

            We regret to inform you that your mental health record requires additional information or clarification.

            Review Details:
            - Date Reviewed: {record.reviewed_at.strftime('%B %d, %Y')}
            - Status: Additional Information Required
            - Reviewer: {record.reviewed_by.get_full_name()}

            Document Review:
            - Prescription Document: {prescription_remarks if prescription_remarks else 'No remarks provided'}
            - Certification Document: {certification_remarks if certification_remarks else 'No remarks provided'}

            Additional Notes:
            {notes if notes else 'No specific reason provided.'}

            Please submit the required information or clarification through the student portal.

            Best regards,
            Medical Services Team
            """
        elif status == 'pending':
            subject = 'Mental Health Record - Status Updated'
        message = f"""
        Dear {record.patient.student.firstname},
        
            Your mental health record status has been updated to pending review.

            Review Details:
            - Date Updated: {record.reviewed_at.strftime('%B %d, %Y')}
            - Status: Pending Review
            - Updated By: {record.reviewed_by.get_full_name()}

            Document Review:
            - Prescription Document: {prescription_remarks if prescription_remarks else 'Under Review'}
            - Certification Document: {certification_remarks if certification_remarks else 'Under Review'}

            Additional Notes:
            {notes if notes else 'No additional notes provided.'}

            We will notify you once the review is complete.
        
        Best regards,
        Medical Services Team
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [record.patient.student.email],
                fail_silently=False,
            )
            messages.success(request, 'Record reviewed successfully and notification sent.')
        except Exception as e:
            messages.error(request, f'Record reviewed but failed to send email: {str(e)}')
        
        return redirect('main:mental_health')
        
    return render(request, 'admin/mental_health_review.html', {'record': record})

def logout_view(request):
    logout(request)
    return redirect('main:login')

def email_verification(request):
    return render(request, 'email_verification.html')

@login_required
def upload_profile_picture_view(request):
    if request.method == 'POST' and request.FILES.get('profile_picture'):
        try:
            student = Student.objects.get(email=request.user.email)
            student.profile_picture = request.FILES['profile_picture']
            student.save()
            return JsonResponse({'status': 'success'})
        except Student.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Student profile not found'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})