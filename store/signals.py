from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
import logging

from .models import CustomUser, Order

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
        except Exception:
            logger.exception('Failed to send staff-removal email to %s', instance.email)


# ---- Order payment signals: send invoice when payment_status becomes 'paid' ----
@receiver(pre_save, sender=Order)
def _order_pre_save(sender, instance, **kwargs):
    """Store previous payment_status on the instance for comparison in post_save."""
    if not instance.pk:
        # New order; nothing to fetch
        instance._previous_payment_status = None
        return
    try:
        previous = Order.objects.get(pk=instance.pk)
        instance._previous_payment_status = previous.payment_status
    except Order.DoesNotExist:
        instance._previous_payment_status = None


@receiver(post_save, sender=Order)
def _order_post_save(sender, instance, created, **kwargs):
    """When an Order's payment_status transitions to 'paid', send the invoice email."""
    try:
        prev = getattr(instance, '_previous_payment_status', None)
        new = getattr(instance, 'payment_status', None)
        # If newly paid (including created as paid), and previous wasn't 'paid'
        if new == 'paid' and prev != 'paid':
            try:
                # Send synchronously to guarantee delivery when payment_status becomes 'paid'
                from .views import _send_order_email
                _send_order_email(instance, 'invoice', f'Invoice - {settings.SITE_NAME} - {instance.order_number}', instance.user.email, request=None)
            except Exception:
                logger.exception('Failed to send invoice synchronously for order %s', instance.order_number)
    except Exception:
        logger.exception('Error in order post-save signal for order %s', getattr(instance, 'order_number', 'N/A'))
