from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_verification_email(user, verification):
    """
    Send verification email to user
    """
    subject = 'Verify your HealthHub Connect account'
    
    # Create verification URL
    verification_url = f"{settings.SITE_URL}/verify-email/{verification.token}"
    
    # Render email template
    html_message = render_to_string('email/verification_email.html', {
        'user': user,
        'verification_url': verification_url,
    })
    
    # Strip HTML for plain text version
    plain_message = strip_tags(html_message)
    
    # Send email
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )

def send_password_reset_email(user, reset_token):
    """
    Send password reset email to user
    """
    subject = 'Reset your HealthHub Connect password'
    
    # Create reset URL
    reset_url = f"{settings.SITE_URL}/password-reset/{reset_token}"
    
    # Render email template
    html_message = render_to_string('email/password_reset_email.html', {
        'user': user,
        'reset_url': reset_url,
    })
    
    # Strip HTML for plain text version
    plain_message = strip_tags(html_message)
    
    # Send email
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    ) 