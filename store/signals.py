from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
import logging

from .models import CustomUser

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=CustomUser)
def notify_on_staff_removal(sender, instance, **kwargs):
    """Send an official email when a user's role changes from 'staff' to a non-staff role."""
    # Only proceed for existing users (skip creations)
    if not instance.pk:
        return

    try:
        previous = CustomUser.objects.get(pk=instance.pk)
    except CustomUser.DoesNotExist:
        return

    prev_role = getattr(previous, 'role', None)
    new_role = getattr(instance, 'role', None)

    if prev_role == 'staff' and new_role != 'staff':
        # Prepare simple plain-text notification
        subject = 'Staff access removed — Fishy Friend Aquatics'
        name = instance.get_full_name() or instance.username
        body = (
            f"Hello {name},\n\n"
            "This is an official notification from Fishy Friend Aquatics. "
            "Your staff access has been removed and your account role has been changed. "
            "If you believe this is an error, please contact an administrator immediately.\n\n"
            "If you have questions, reply to this email or contact support.\n\n"
            "— Fishy Friend Aquatics Team"
        )

        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None)
        recipient = [instance.email] if instance.email else []

        if not recipient:
            logger.warning('User %s has no email set; cannot send staff-removal notification.', instance.pk)
            return

        try:
            send_mail(subject, body, from_email, recipient, fail_silently=False)
            logger.info('Sent staff-removal email to %s', instance.email)
        except Exception:
            logger.exception('Failed to send staff-removal email to %s', instance.email)
