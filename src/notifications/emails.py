from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import Template, Context

from auditlogs.models import EmailLog
from notifications.models import Notification



def send_submitted_notification(context):
    send_notification(
        Notification.NotificationType.SUBMISSION,
        context,
    )


def send_modified_by_apr(context):
    send_notification(
        Notification.NotificationType.APR_MODIFICATION,
        context,
    )


def send_reminders(context):
    send_notification(
        Notification.NotificationType.REMINDER,
        context,
    )


def send_notification(notification_type, context):
    notification = Notification.objects.get(name=notification_type)

    recipients = notification.get_recipients(context)

    subject = render_notification_template(
        notification.subject,
        context,
    )

    body = render_notification_template(notification.body, context)

    email_log = EmailLog.objects.create(
        notification_type=str(notification_type),
        subject=subject,
        recipients={
            "to": recipients["to"],
            "cc": recipients["cc"],
            "bcc": recipients["bcc"],
        },
    )

    email = EmailMultiAlternatives(
        subject=subject,
        body="",
        to=recipients["to"],
        cc=recipients["cc"],
        bcc=recipients["bcc"],
        from_email=settings.DEFAULT_FROM_EMAIL,
    )

    email.attach_alternative(body, "text/html")

    try:
        sent = email.send(fail_silently=False)

        if sent == 1:
            email_log.status = EmailLog.Status.SENT
        else:
            email_log.status = EmailLog.Status.FAILED
            email_log.error_message = "Email backend did not send the email."

    except Exception as exc:
        email_log.status = EmailLog.Status.FAILED
        email_log.error_message = str(exc)

    finally:
        email_log.save(update_fields=["status", "error_message"])


def render_notification_template(text, context):
    return Template(text).render(Context(context))
