from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Student, EmailVerification

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


class CustomUserAdmin(UserAdmin):
    form = UserAdminForm
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_email_verified_method')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', EmailVerifiedFilter)
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    # is_email_verified_method is used for display in list_display and potentially readonly_fields
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


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'lrn', 'lastname', 'firstname', 'degree', 'year_level')
    list_filter = ('degree', 'year_level', 'sex')
    search_fields = ('student_id', 'lrn', 'lastname', 'firstname', 'email')
    ordering = ('lastname', 'firstname')
    
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
