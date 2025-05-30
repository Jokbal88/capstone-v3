from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from main.models import Student, EmailVerification, Profile, Faculty
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
        print("Received POST request in register view.")
        print("POST data:", request.POST)
        try:
            # Get common form data first
            firstName = request.POST.get("firstName")
            middleInitial = request.POST.get("middleInitial")
            lastName = request.POST.get("lastName")
            email = request.POST.get("email")
            password = request.POST.get("password")
            confirmPassword = request.POST.get("confirmPassword")
            role = request.POST.get("role", 'Student') # Get selected role, default to Student

            print("Received role:", role)

            # Check if email already exists (common validation)
            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Email already registered.'
                })

            # Validate password (common validation)
            if password != confirmPassword:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Passwords do not match.'
                })

            if role == 'Student':
                # Get student-specific data
                sex = request.POST.get("sex")
                yrLevel = request.POST.get("yrLevel")
                id_numbers = request.POST.getlist("idNumber")
                idNumber = next((id_num for id_num in id_numbers if id_num), id_numbers[-1] if id_numbers else '')
                lrn = request.POST.get("lrn")
                course = request.POST.get("course")

                print("Received LRN for student:", lrn)
                print(f"firstName: {firstName}")
                print(f"middleInitial: {middleInitial}")
                print(f"lastName: {lastName}")
                print(f"sex: {sex}")
                print(f"yrLevel: {yrLevel}")
                print(f"idNumber: {idNumber}")
                print(f"lrn: {lrn}")
                print(f"course: {course}")
                print(f"email: {email}")
                print(f"password: {password}")
                print(f"confirmPassword: {confirmPassword}")

                # Validate required fields for students
                if not all([firstName, lastName, sex, yrLevel, idNumber, lrn, course, email, password, confirmPassword]):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Please provide all required student information.'
                    })

                # Validate LRN format
                if not lrn or not lrn.isdigit() or len(lrn) != 12:
                    print("LRN validation failed for student.")
                    return JsonResponse({
                        'status': 'error',
                        'message': 'LRN must be exactly 12 digits.'
                    })

                # Validate Student ID Number format
                if not idNumber or not idNumber.isdigit() or len(idNumber) != 7:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'ID Number must be exactly 7 digits.'
                    })

                # Check if student ID already exists
                if Student.objects.filter(student_id=idNumber).exists():
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Student ID already registered.'
                    })

                # Check if LRN already exists
                if Student.objects.filter(lrn=lrn).exists():
                    return JsonResponse({
                        'status': 'error',
                        'message': 'LRN already registered.'
                    })

                # Create user
                user = User.objects.create_user(
                    username=email, # Using email as username
                    email=email,
                    password=password,
                    first_name=firstName,
                    last_name=lastName,
                )

                # Create Profile for the user
                profile = Profile.objects.create(user=user, role=role)

                # Create Student instance
                student_instance = Student.objects.create(
                    student_id=idNumber,
                    lrn=lrn,
                    lastname=lastName,
                    firstname=firstName,
                    middlename=middleInitial,
                    degree=course,
                    year_level=int(yrLevel),
                    sex=sex,
                    email=email,
                    contact_number='N/A'
                )

                # Create Patient instance and link to the User
                Patient.objects.create(user=user)

            elif role == 'Faculty':
                # Get faculty-specific data
                department = request.POST.get('department')
                position = request.POST.get('position')
                faculty_id = request.POST.get('idNumber')
                sex = request.POST.get('sex')
                middlename = request.POST.get('middleInitial')

                # Validate required fields for faculty
                if not all([firstName, middleInitial, lastName, department, position, faculty_id, sex, email, password, confirmPassword]):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Please provide all required faculty information (First Name, Middle Initial, Last Name, Department, Position, ID Number, Sex, Email, Password, Confirm Password).'
                    })

                # Optional validation for faculty ID format
                if not faculty_id.isdigit() or len(faculty_id) != 7:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Faculty ID Number must be exactly 7 digits.'
                    })

                # Check if faculty ID already exists
                if Faculty.objects.filter(faculty_id=faculty_id).exists():
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Faculty ID already registered.'
                    })

                # Create user
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=firstName,
                    last_name=lastName,
                )

                # Create Profile for the user
                profile = Profile.objects.create(user=user, role=role)

                # Create Faculty instance
                Faculty.objects.create(
                    user=user,
                    faculty_id=faculty_id,
                    department=department,
                    position=position,
                    sex=sex,
                    middlename=middlename
                )

                # Create Patient instance and link to the User
                Patient.objects.create(user=user)

            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid role specified.'
                })

            # If registration is successful for either role
            return JsonResponse({
                'status': 'success',
                'message': 'Registration successful. Please log in to verify your email.'
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })

    # For GET request, render the registration form
    return render(request, "register.html")

def verify_otp(request):
    if request.method == 'POST':
        email = request.session.get('verification_email')
        otp = request.POST.get('otp')
        
        print(f"Received OTP verification request for email: {email}")
        print(f"Entered OTP: {otp}")
        
        if not email:
            print("No verification email found in session")
            return JsonResponse({
                'status': 'error',
                'message': 'No verification session found. Please try logging in again.'
            })
        
        try:
            user = User.objects.get(email=email)
            verification = EmailVerification.objects.get(user=user)
            
            print(f"Found user: {user.username}")
            print(f"Stored OTP: {verification.otp}")
            print(f"OTP created at: {verification.created_at}")
            
            if verification.is_otp_expired():
                print("OTP has expired")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Verification code has expired. Please request a new one.'
                })
            
            if verification.otp == otp:
                print("OTP matched successfully")
                verification.is_verified = True
                verification.save()
                
                # Log the user in
                login(request, user)
                print(f"User {user.username} logged in successfully")
                
                # Clear the verification session
                if 'verification_email' in request.session:
                    del request.session['verification_email']
                
                # Determine redirect URL based on user role
                if user.is_superuser or user.is_staff:
                    redirect_url = reverse('main:admin_dashboard')
                else:
                    redirect_url = reverse('main:main')
                
                # Return success with appropriate redirect URL
                return JsonResponse({
                    'status': 'success',
                    'message': 'OTP verified successfully.',
                    'redirect_url': redirect_url
                })
            else:
                print(f"OTP mismatch. Stored OTP: {verification.otp}, Received OTP: {otp}")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid verification code.'
                })
                
        except User.DoesNotExist:
            print(f"User not found for email: {email}")
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid email address.'
            })
        except EmailVerification.DoesNotExist:
            print(f"EmailVerification not found for user with email: {email}")
            return JsonResponse({
                'status': 'error',
                'message': 'Verification record not found. Please try logging in again.'
            })
        except Exception as e:
            print(f"Unexpected error during OTP verification: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'An unexpected error occurred. Please try again.'
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
    print(f"Entering main_view for user: {request.user.username}")
    # Check if the user is authenticated (already done by @login_required, but good practice)
    if request.user.is_authenticated:
        profile_complete = False # Assume incomplete initially
        try:
            print(f"Checking profile completion for user: {request.user.username}")
            # Get the Patient record for the current user
            patient = medical_models.Patient.objects.get(user=request.user)
            print(f"Found patient record for user: {request.user.username}")

            # Check for existence of related medical records
            try:
                physical_exam = patient.examination
                print(f"Found physical examination for patient")
                
                # Check medical history
                try:
                    medical_history = physical_exam.medicalhistory
                    print("Found medical history")
                except medical_models.MedicalHistory.DoesNotExist:
                    print("Medical history not found")
                    profile_complete = False
                    raise

                # Check family history
                try:
                    family_history = physical_exam.familymedicalhistory
                    print("Found family medical history")
                except medical_models.FamilyMedicalHistory.DoesNotExist:
                    print("Family medical history not found")
                    profile_complete = False
                    raise

                # Check risk assessment
                try:
                    risk_assessment = medical_models.RiskAssessment.objects.get(clearance=patient)
                    print("Found risk assessment")
                except medical_models.RiskAssessment.DoesNotExist:
                    print("Risk assessment not found")
                    profile_complete = False
                    raise

                # If we get here, all records exist
                profile_complete = True
                print("Profile is complete")

            except Exception as e:
                print(f"Error checking medical records: {str(e)}")
                profile_complete = False

            except medical_models.Patient.DoesNotExist:
                print(f"No patient record found for user: {request.user.username}")
                profile_complete = False

        except Exception as e:
            print(f"Unexpected error during profile check in main_view: {str(e)}")
            messages.error(request, 'An unexpected error occurred while verifying your profile status.')
            return redirect('main:login')

        print(f"Profile completion status: {profile_complete}")
        if not profile_complete:
            print("Redirecting to patient form due to incomplete profile")
            messages.info(request, 'Please complete your medical profile first.')
            return redirect('main:patient_form')
        else:
            print("Profile is complete, redirecting to appropriate dashboard")
            if hasattr(request.user, 'profile') and request.user.profile.role == 'Faculty':
                return redirect('main:faculty_dashboard')
            else:
                return redirect('main:student_dashboard')
    else:
        print("User is not authenticated in main_view")
    return redirect('main:login')

@login_required
def patient_form(request):
    # Try to get the Patient record for the current user
    try:
        patient = medical_models.Patient.objects.get(user=request.user)
    except medical_models.Patient.DoesNotExist:
        # If no patient record exists, create one and link it to the user
        print("Patient object does not exist. Creating a new one.")
        patient = medical_models.Patient.objects.create(user=request.user)
        # A message might be helpful here to inform the user that a new record was created
        messages.info(request, "A new medical profile record has been created for your account. Please fill out the form.")

    if request.method == 'GET':
        profile_complete = True # Assume complete initially, prove otherwise
        try:
            # Check for the existence of essential linked medical records sequentially
            if not patient.examination:
                print("PatientForm GET: PhysicalExamination does not exist.")
                profile_complete = False
            else:
                physical_exam = patient.examination
                try:
                    # Check MedicalHistory linked via PhysicalExamination
                    medical_history = physical_exam.medicalhistory

                    # Check FamilyMedicalHistory linked via PhysicalExamination
                    family_history = physical_exam.familymedicalhistory

                    # Check RiskAssessment linked directly to Patient
                    risk_assessment = patient.riskassessment

                    # If we reached here, all essential related objects exist
                    # profile_complete remains True

                except medical_models.MedicalHistory.RelatedObjectDoesNotExist:
                    print(f"PatientForm GET: Missing related medical record: {e}")
                    profile_complete = False # Explicitly set to False if any related object is missing
                except Exception as e:
                    print(f"PatientForm GET: Unexpected error checking related medical records: {e}")
                    profile_complete = False # Treat unexpected errors as incomplete profile

        except medical_models.Patient.DoesNotExist:
            # This exception should ideally be caught by the outer try-except,
            # but including for robustness in this nested structure if needed.
            print("PatientForm GET: Patient object does not exist in nested check.")
            profile_complete = False
        except Exception as e:
            print(f"PatientForm GET: Unexpected error getting patient object: {e}")
            profile_complete = False # Treat unexpected errors as incomplete

        if profile_complete:
            messages.info(request, 'Your medical profile is already complete.')
            # Redirect based on user role
            if hasattr(request.user, 'profile') and request.user.profile.role == 'Faculty':
                return redirect('main:faculty_dashboard')
            else:
                return redirect('main:student_dashboard')

        # If profile is incomplete, render the form
        today = date.today()
        context = {
            'current_date': today,
            'patient': patient, # Pass the patient object to pre-fill the form if data exists
        }
        return render(request, 'patient_form.html', context)

    if request.method == 'POST':
        try:
            # Update the existing Patient record with form data
            patient = medical_models.Patient.objects.get(user=request.user)
            patient.birth_date = request.POST.get('birth_date')
            patient.age = calculate_age(request.POST.get('birth_date')) if patient.birth_date else None
            patient.weight = float(request.POST.get('weight')) if request.POST.get('weight') else None
            patient.height = float(request.POST.get('height')) if request.POST.get('height') else None
            patient.bloodtype = request.POST.get('bloodtype')
            patient.allergies = process_checkboxes(request.POST.getlist('allergies'), request.POST.get('other_allergies'))
            patient.medications = request.POST.get('medications', '')
            patient.home_address = request.POST.get('home_address')
            patient.city = request.POST.get('city')
            patient.state_province = request.POST.get('state_province')
            patient.postal_zipcode = request.POST.get('postal_zipcode')
            patient.country = request.POST.get('country')
            patient.nationality = request.POST.get('nationality')
            patient.civil_status = request.POST.get('civil_status')
            num_children_str = request.POST.get('number_of_children')
            patient.number_of_children = int(num_children_str) if num_children_str and num_children_str.isdigit() else None

            if not patient.academic_year:
                patient.academic_year = f"{timezone.now().year}-{timezone.now().year + 1}"

            patient.section = request.POST.get('section', '')
            patient.parent_guardian = request.POST.get('parent_guardian')
            patient.parent_guardian_contact_number = request.POST.get('parent_guardian_contact', '')

            patient.save() # Save updated patient info first

            # --- Physical Examination logic --- 
            # Get or create PhysicalExamination linked to the patient
            physical_exam, _ = medical_models.PhysicalExamination.objects.get_or_create(patient=patient)
            exam_date_str = request.POST.get('date_of_physical_examination')
            if exam_date_str:
                physical_exam.date_of_physical_examination = exam_date_str
            else:
                if not physical_exam.date_of_physical_examination:
                    physical_exam.date_of_physical_examination = timezone.now().strftime('%Y-%m-%d')
            physical_exam.save()

            # Link the examination to the patient if it wasn't already linked
            if not patient.examination:
                patient.examination = physical_exam
                patient.save() # Save patient again to establish the link
            
            # --- Medical History logic ---
            med_hist_list = request.POST.getlist('medical_history')
            # Get or create MedicalHistory linked to the physical_exam
            medical_history, _ = medical_models.MedicalHistory.objects.get_or_create(examination=physical_exam)
            medical_history.tuberculosis = 'tuberculosis' in med_hist_list
            medical_history.hypertension = 'hypertension' in med_hist_list
            medical_history.heart_disease = 'heart_disease' in med_hist_list
            medical_history.hernia = 'hernia' in med_hist_list
            medical_history.epilepsy = 'epilepsy' in med_hist_list
            medical_history.peptic_ulcer = 'peptic_ulcer' in med_hist_list
            medical_history.kidney_disease = 'kidney_disease' in med_hist_list
            medical_history.asthma = 'asthma' in med_hist_list
            medical_history.insomnia = 'insomnia' in med_hist_list
            medical_history.malaria = 'malaria' in med_hist_list
            medical_history.venereal_disease = 'venereal_disease' in med_hist_list
            medical_history.nervous_breakdown = 'nervous_breakdown' in med_hist_list
            medical_history.jaundice = 'jaundice' in med_hist_list
            medical_history.others = request.POST.get('other_medical', '')
            medical_history.no_history = 'No Medical History' in med_hist_list
            medical_history.save()

            # --- Family Medical History logic ---
            fam_hist_list = request.POST.getlist('family_history')
            # Get or create FamilyMedicalHistory linked to the physical_exam
            family_history, _ = medical_models.FamilyMedicalHistory.objects.get_or_create(examination=physical_exam)
            family_history.hypertension = 'hypertension' in fam_hist_list
            family_history.asthma = 'asthma' in fam_hist_list
            family_history.cancer = 'cancer' in fam_hist_list
            family_history.tuberculosis = 'tuberculosis' in fam_hist_list
            family_history.diabetes = 'diabetes' in fam_hist_list
            family_history.bleeding_disorder = 'bleeding_disorder' in fam_hist_list
            family_history.epilepsy = 'epilepsy' in fam_hist_list
            family_history.mental_disorder = 'mental_disorder' in fam_hist_list
            family_history.no_history = 'No Family History' in fam_hist_list
            family_history.other_medical_history = request.POST.get('other_family_medical', '')
            family_history.save()

            # --- Risk Assessment logic ---
            risk_list = request.POST.getlist('risk_assessment')
            # Get or create RiskAssessment linked to the patient
            risk_assessment, _ = medical_models.RiskAssessment.objects.get_or_create(clearance=patient)
            risk_assessment.cardiovascular_disease = 'cardiovascular' in risk_list
            risk_assessment.chronic_lung_disease = 'chronic_lung' in risk_list
            risk_assessment.chronic_renal_disease = 'chronic_kidney' in risk_list
            risk_assessment.chronic_liver_disease = 'chronic_liver' in risk_list
            risk_assessment.cancer = 'cancer' in risk_list
            risk_assessment.autoimmune_disease = 'autoimmune' in risk_list
            risk_assessment.pwd = 'pwd' in risk_list
            risk_assessment.disability = request.POST.get('disability', '')
            risk_assessment.save()

            # After successfully saving all related data and linking examination, redirect
            messages.success(request, 'Medical information submitted successfully!')
            # Redirect based on user role
            if hasattr(request.user, 'profile') and request.user.profile.role == 'Faculty':
                return redirect('main:faculty_dashboard')
            else:
                return redirect('main:student_dashboard')
            
        except Exception as e:
            print(f"Error saving patient information: {e}")
            messages.error(request, f'Error saving patient information: {str(e)}')
        today = date.today()
        context = {
            'current_date': today,
            'patient': patient, # Pass the patient object back to the form on error
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
    
    # Get all requests with patient and user information
    upcoming_requests = PatientRequest.objects.select_related(
        'patient',
        'patient__user'
    ).order_by('date_requested')
    
    # Get dental service requests
    dental_requests = DentalRecords.objects.select_related(
        'patient',
        'patient__user'
    ).filter(appointed=False).order_by('date_requested')
    
    # Get scheduled appointments for the calendar
    scheduled_appointments = PatientRequest.objects.select_related(
        'patient',
        'patient__user'
    ).values(
        'date_requested',
        'approve',
        'patient__user__first_name',
        'patient__user__last_name',
        'request_type'
    )
    
    # Format appointments for the calendar
    events = []
    for appointment in scheduled_appointments:
        events.append({
            'date': appointment['date_requested'].strftime('%Y-%m-%d'),
            'student': f"{appointment['patient__user__first_name']} {appointment['patient__user__last_name']}",
            'service': appointment['request_type'],
            'status': 'approved' if appointment['approve'] else 'pending'
        })
    
    # Example: Urgent cases (patients with allergies or chronic conditions)
    urgent_cases = Patient.objects.filter(allergies__isnull=False).count()
    
    # Emergency Assistance Requests
    emergency_requests = PatientRequest.objects.select_related(
        'patient',
        'patient__user'
    ).filter(request_type__icontains='emergency').order_by('date_requested')
    
    # Mental Health Requests
    mental_health_requests = MentalHealthRecord.objects.select_related(
        'patient',
        'patient__user'
    ).order_by('-date_submitted')
    
    # Get prescription requests
    prescription_requests = PrescriptionRecord.objects.select_related(
        'patient',
        'patient__user'
    ).order_by('-date_prescribed')
    
    # Notifications
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
        # Get the Patient record linked to the logged-in User
        patient = medical_models.Patient.objects.get(user=request.user)

        # Get related medical data through the patient object
        # Check if physical examination exists before trying to access related models
        physical_exam = None
        medical_history = None
        family_history = None
        risk_assessment = None
        patient_requests = None

        if patient.examination:
            physical_exam = patient.examination
            # Now get related models through physical_exam if it exists
            medical_history = medical_models.MedicalHistory.objects.filter(examination=physical_exam).first()
            family_history = medical_models.FamilyMedicalHistory.objects.filter(examination=physical_exam).first()
            # Risk assessment is linked to Patient through clearance field
            try:
                risk_assessment = medical_models.RiskAssessment.objects.get(clearance=patient)
            except medical_models.RiskAssessment.DoesNotExist:
                risk_assessment = None

            # Get patient requests (linked to Patient directly)
            patient_requests = PatientRequest.objects.filter(patient=patient).order_by('-date_requested')
            
        # Get student information
        student = None
        try:
            student = Student.objects.get(email=request.user.email)
        except Student.DoesNotExist:
            # Handle cases where a Student object might not exist for this user (e.g., faculty)
            pass

        context = {
            'user': request.user,
            'student': student,
            'patient': patient,
            'medical_history': medical_history,
            'family_history': family_history,
            'risk_assessment': risk_assessment,
            'physical_exam': physical_exam,
            'patient_requests': patient_requests,
            'medical_profile_incomplete': not patient.examination
        }
            
        return render(request, 'student_dashboard.html', context)
            
    except medical_models.Patient.DoesNotExist:
        messages.info(request, 'Your medical profile is incomplete. Please complete it.')
        return render(request, 'student_dashboard.html', {'medical_profile_incomplete': True})
    except Exception as e:
        print(f"Error in dashboard_view: {e}")
        messages.error(request, 'Error loading dashboard data.')
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

@login_required
def faculty_dashboard_view(request):
    if not request.user.profile.role == 'Faculty':
        messages.error(request, 'Access denied. Faculty access only.')
        return redirect('main:login')

    try:
        # Get faculty information
        faculty = Faculty.objects.get(user=request.user)
        
        # Get the Patient record for the faculty user
        patient = medical_models.Patient.objects.get(user=request.user)
        medical_profile_incomplete = not patient.examination
    except (Faculty.DoesNotExist, medical_models.Patient.DoesNotExist):
        messages.error(request, 'Faculty profile not found.')
        return redirect('main:login')

    # Get total students count
    total_students = Student.objects.count()
    
    # Get pending requests
    pending_requests = PatientRequest.objects.filter(approve=False).count()
    
    # Get today's appointments
    today = timezone.now().date()
    todays_appointments = PatientRequest.objects.filter(
        date_requested__date=today,
        approve=True
    ).count()
    
    # Get recent requests with student information
    recent_requests = PatientRequest.objects.select_related(
        'patient__user'
    ).order_by('-date_requested')[:10]
    
    # Get appointments for calendar
    appointments = PatientRequest.objects.select_related(
        'patient__user'
    ).filter(approve=True).order_by('date_requested')
    
    # Format appointments for the calendar
    calendar_events = []
    for appointment in appointments:
        try:
            student = Student.objects.get(email=appointment.patient.user.email)
            calendar_events.append({
                'title': f"{student.firstname} {student.lastname}",
                'start': appointment.date_requested.strftime('%Y-%m-%d'),
                'description': appointment.request_type
            })
        except Student.DoesNotExist:
            continue  # Skip if student not found
    
    # Get faculty's medical information
    physical_exam = patient.examination if patient.examination else None
    medical_history = None
    family_history = None
    risk_assessment = None

    if physical_exam:
        try:
            medical_history = medical_models.MedicalHistory.objects.get(examination=physical_exam)
            family_history = medical_models.FamilyMedicalHistory.objects.get(examination=physical_exam)
            risk_assessment = medical_models.RiskAssessment.objects.get(clearance=patient)
        except (medical_models.MedicalHistory.DoesNotExist, 
                medical_models.FamilyMedicalHistory.DoesNotExist,
                medical_models.RiskAssessment.DoesNotExist):
            pass
    
    context = {
        'faculty': faculty,
        'patient': patient,
        'medical_history': medical_history,
        'family_history': family_history,
        'risk_assessment': risk_assessment,
        'physical_exam': physical_exam,
        'total_students': total_students,
        'pending_requests': pending_requests,
        'todays_appointments': todays_appointments,
        'recent_requests': recent_requests,
        'appointments': calendar_events,
        'medical_profile_incomplete': medical_profile_incomplete,
    }
    
    return render(request, 'faculty_dashboard.html', context)