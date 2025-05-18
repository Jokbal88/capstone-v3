from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from main.models import Student
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
from medical import forms as medical_forms

def is_admin(user):
    return user.is_staff

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        
        if user is None:
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is not None:
            login(request, user)
            
            #kani nga condition siguro ang issue
            redirect_url = 'main:main' if user.is_staff or user.is_superuser else 'main:patient_form'
            
            
            return JsonResponse({
                'status': 'success',
                'redirect_url': reverse(redirect_url)
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid ID number/Email or password'
            })

    return render(request, 'login.html')

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

            # Create User account
            user = User.objects.create_user(
                username=student_id,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Create Student in main app only
            Student.objects.create(
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

            messages.success(request, 'Registration successful! Please complete your medical profile.')
            return redirect('main:login')

        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
            return redirect('main:register')

    return render(request, 'register.html')

def recovery(request):
    return render(request, 'recovery.html')

def password_reset(request):
    return render(request, 'password-reset.html')


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
    if request.method == 'POST':
        try:
            patient = medical_models.Patient.objects.get(student_id=request.user.username)
            messages.error(request, "You have already submitted your patient information.")
            return redirect('main:main')
        except medical_models.Patient.DoesNotExist:
            # Process the form submission
            form = medical_forms.PatientForm(request.POST)
            if form.is_valid():
                patient = form.save(commit=False)
                patient.student = request.user
                patient.save()
                messages.success(request, "Patient information submitted successfully.")
                return redirect('main:main')
            else:
                messages.error(request, "Please correct the errors below.")
    else:
        try:
            patient = medical_models.Patient.objects.get(student_id=request.user.username)
            messages.error(request, "You have already submitted your patient information.")
            return redirect('main:main')
        except medical_models.Patient.DoesNotExist:
            form = medical_forms.PatientForm()
    
    return render(request, 'patient_form.html', {'form': form})

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