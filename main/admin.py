from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Student, EmailVerification, Faculty, Profile

class EmailVerifiedFilter(admin.SimpleListFilter):
    title = _('email verified')
    parameter_name = 'email_verified'

    def lookups(self, request, model_admin):
        return [
            ('yes', _('Yes')),
            ('no', _('No')),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            # Filter for users with a related EmailVerification object that is verified
            return queryset.filter(email_verification__is_verified=True)
        if self.value() == 'no':
            # Filter for users without a related EmailVerification object OR with one that is not verified
            # We use Q objects for a more robust query
            from django.db.models import Q
            return queryset.filter(Q(email_verification__isnull=True) | Q(email_verification__is_verified=False))
        return queryset

class UserAdminForm(forms.ModelForm):
    is_email_verified_field = forms.BooleanField(
        label=_('Email Verified'),
        required=False,
        help_text=_('Designates whether the user\'s email address has been verified.'),
    )

    class Meta:
        model = User
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            try:
                verification = EmailVerification.objects.get(user=self.instance)
                self.initial['is_email_verified_field'] = verification.is_verified
            except EmailVerification.DoesNotExist:
                self.initial['is_email_verified_field'] = False

    def save(self, commit=True):
        # Save the User object without committing immediately
        user = super().save(commit=False)

        # Update the EmailVerification status
        is_verified = self.cleaned_data.get('is_email_verified_field', False)
        verification, created = EmailVerification.objects.get_or_create(user=user)
        verification.is_verified = is_verified
        verification.save()

        # Return the user instance for the admin to save and handle m2m
        if commit:
            user.save()
        return user

# Register Profile model
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'

# Extend UserAdmin to include Profile
class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    form = UserAdminForm
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__role', EmailVerifiedFilter)
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    readonly_fields = ('is_email_verified_method',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'is_email_verified_field', 'is_email_verified_method')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser',
                       'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    def is_email_verified_method(self, obj):
        try:
            verification = EmailVerification.objects.get(user=obj)
            return verification.is_verified
        except EmailVerification.DoesNotExist:
            return False
    is_email_verified_method.boolean = True
    is_email_verified_method.short_description = _('Email Verified (Display)')

    def get_role(self, obj):
        return obj.profile.role if hasattr(obj, 'profile') else '-'
    get_role.short_description = 'Role'

# Register Student model
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'lastname', 'firstname', 'degree', 'year_level', 'email')
    list_filter = ('year_level', 'degree', 'sex')
    search_fields = ('student_id', 'lastname', 'firstname', 'email', 'lrn')
    ordering = ('lastname', 'firstname')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(pk__in=self.model.objects.values_list('pk', flat=True))
    
    fieldsets = (
        ('Personal Information', {
            'fields': (
                'student_id', 
                'lrn',
                ('lastname', 'firstname', 'middlename'),
                'sex',
            )
        }),
        ('Academic Information', {
            'fields': (
                'degree',
                'year_level',
            )
        }),
        ('Contact Information', {
            'fields': (
                'email',
                'contact_number',
            )
        }),
    )

# Register Faculty model
@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('get_name', 'department', 'position', 'created_at')
    list_filter = ('department', 'position')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'department', 'position')
    ordering = ('user__last_name', 'user__first_name')

    def get_name(self, obj):
        return f"{obj.user.get_full_name()}"
    get_name.short_description = 'Name'

# Register EmailVerification model
@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'is_verified')
    list_filter = ('is_verified', 'created_at')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('created_at',)

# Unregister the default UserAdmin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
