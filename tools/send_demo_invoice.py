"""Send a demo invoice email for the most recent paid order (or latest order).

This script expects Django to be configured and `django.setup()` already called
by the caller. It is safe to import project code after setup.

Usage (from project root):
python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','fishy_friend_aquatics.settings'); import django; django.setup(); exec(open('tools/send_demo_invoice.py').read())"
"""

import logging
import sys
import traceback

logger = logging.getLogger(__name__)

try:
    from store.models import Order
    from store.views import _send_order_email
    from django.conf import settings
except Exception:
    logger.exception('Failed to import app modules; ensure this is run after django.setup()')
    raise


def main():
    try:
        # Prefer most recently paid order
        order = Order.objects.filter(payment_status='paid').order_by('-updated_at')
        if not order.exists():
            # Fallback: any order
            order = Order.objects.all().order_by('-created_at')
        order = order.first()

        if not order:
            print('No orders found in the database. Create an order first.')
            return

        recipient = order.user.email or getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        if not recipient:
            print('Order has no recipient email and DEFAULT_FROM_EMAIL not set.')
            return

        subject = f'Invoice - {getattr(settings, "SITE_NAME", "Aquafish Store")} - {order.order_number}'
        print(f'Sending invoice for order {order.order_number} to {recipient}')

        # Synchronously send using the project's helper (it will generate and attach PDF as configured)
        try:
            _send_order_email(order, 'invoice', subject, recipient, request=None)
            print(f'Sent order email invoice for order {order.order_number} to {recipient}')
        except Exception:
            print('Failed sending invoice. See traceback below:')
            traceback.print_exc()

    except Exception:
        logger.exception('Unexpected error in send_demo_invoice')
        traceback.print_exc()


if __name__ == '__main__':
    main()
