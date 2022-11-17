import smtplib
from myset.celery import app
from django.conf import settings
from django.core.mail import send_mail, BadHeaderError
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode
from .models import User
from .tokens import account_activation_token


@app.task(bind=True, default_retry_delay=1 * 60)
def send_verification_email(self, user_id: int) -> None:
    """Celery task to send account verification link to user's email address."""

    user = User.objects.get(id=user_id)
    email_template_name = 'accounts/email/confirm_email.html'
    email_context = {
        'user': user,
        'uid': urlsafe_base64_encode(force_bytes(user_id)),
        'token': account_activation_token.make_token(user),
    }
    mail_subject = 'Activate your account'
    html_message = render_to_string(email_template_name, email_context)
    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject=mail_subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False)
    except smtplib.SMTPException as ex:
        self.retry(exc=ex)
