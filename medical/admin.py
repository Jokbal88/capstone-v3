from django.contrib import admin
from .models import (
    Student, 
    Patient,
    PhysicalExamination,
    MedicalClearance,
    RiskAssessment, 
    MedicalRequirement, 
    PatientRequest, 
    PrescriptionRecord, 
    TransactionRecord, 
    EmergencyHealthAssistanceRecord,
    MedicalHistory,
    FamilyMedicalHistory,
    ObgyneHistory,
    DentalRecords,
    MedicalClearance,
    EligibilityForm,
    MedicalCertificate,
    MentalHealthRecord,
    FacultyRequest
)

# Register your models here.

# class PatientAdmin(admin.ModelAdmin):
#     list_display = ['patient_id_number', 'full_name']

#     def full_name(self, obj):
#         return f"{obj.firstname} {obj.middlename} {obj.surname}"

class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'lastname', 'firstname', 'middlename', 'sex')
    ordering = ('lastname',)
    search_fields = ('student_id',)

class DentalRecordsAdmin(admin.ModelAdmin):
    list_display = ('patient', 'service_type', 'date_requested', 'date_appointed')
    ordering = ('date_requested',)

class PatientRequestAdmin(admin.ModelAdmin):
    list_display = ('patient', 'request_type', 'status', 'date_requested', 'date_responded')
    ordering = ('date_requested',)
    list_filter = ('status', 'request_type')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'request_type')

class FacultyRequestAdmin(admin.ModelAdmin):
    list_display = ('faculty', 'request_type', 'status', 'is_urgent', 'priority_level', 'date_requested', 'date_responded')
    ordering = ('-is_urgent', 'date_requested',)
    list_filter = ('status', 'request_type', 'is_urgent', 'priority_level')
    search_fields = ('faculty__user__first_name', 'faculty__user__last_name', 'request_type')

class EmergencyHealthAssistanceRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'reason', 'date_assisted')
    ordering = ('date_assisted',)

class PrescriptionRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'problem', 'treatment', 'date_prescribed')

class TransactionRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'transac_type', 'transac_date')

class MedicalRequirementAdmin(admin.ModelAdmin):
    list_display = ('patient', 'faculty', 'status', 'reviewed_by', 'reviewed_date')
    search_fields = ('patient__user__username', 'faculty__faculty_id')

class MentalHealthRecordAdmin(admin.ModelAdmin):
    list_filter = ('is_availing_mental_health',)

admin.site.register(Student, StudentAdmin)
admin.site.register(Patient)
admin.site.register(PhysicalExamination)
admin.site.register(MedicalClearance)
admin.site.register(RiskAssessment)
admin.site.register(MedicalRequirement, MedicalRequirementAdmin)
admin.site.register(PatientRequest, PatientRequestAdmin)
admin.site.register(FacultyRequest, FacultyRequestAdmin)
admin.site.register(PrescriptionRecord, PrescriptionRecordAdmin)
admin.site.register(TransactionRecord, TransactionRecordAdmin)
admin.site.register(EmergencyHealthAssistanceRecord, EmergencyHealthAssistanceRecordAdmin)
admin.site.register(MedicalHistory)
admin.site.register(FamilyMedicalHistory)
admin.site.register(ObgyneHistory)
admin.site.register(DentalRecords, DentalRecordsAdmin)
admin.site.register(EligibilityForm)
admin.site.register(MedicalCertificate)
admin.site.register(MentalHealthRecord, MentalHealthRecordAdmin)