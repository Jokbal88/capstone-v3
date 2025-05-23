from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('recovery/', views.recovery, name='recovery'),
    path('password-reset/<str:token>/', views.password_reset, name='password_reset'),
    path('main/', views.main_view, name='main'),
    path('medical/', include('medical.urls', namespace='medical')),
    path('patient-form/', views.patient_form, name='patient_form'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('student-dashboard/', views.dashboard_view, name='student_dashboard'),
    path('mental-health/', views.mental_health_view, name='mental_health'),
    path('mental-health/submit/', views.mental_health_submit, name='mental_health_submit'),
    path('mental-health/review/<int:record_id>/', views.mental_health_review, name='mental_health_review'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('email-verification/', views.email_verification, name='email_verification'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('upload-profile-picture/', views.upload_profile_picture_view, name='upload_profile_picture'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)