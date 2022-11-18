import smtplib
from myset.celery import app
from django.conf import settings
from django.core.mail import send_mail


@app.task(bind=True, default_retry_delay=1 * 60)
def send_email_to_user(self, mail_subject: str, plain_message: str, send_to: list[str],
                       html_message: str = None) -> None:
    """Celery task to send email to user."""

    try:
        send_mail(
            subject=mail_subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=send_to,
            html_message=html_message,
            fail_silently=False,
        )
    except smtplib.SMTPException as ex:
        self.retry(exc=ex)
