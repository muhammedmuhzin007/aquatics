import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fishy_friend_aquatics.settings')
import django
django.setup()

from django.conf import settings
from store.models import Order
from store.views import _send_order_email
import logging

order = Order.objects.filter(payment_method='upi').exclude(payment_status='paid').order_by('-created_at').first()
if not order:
    print('No pending UPI order found to simulate.')
else:
    # Simulate transaction id and mark paid
    order.transaction_id = f"SIM{order.order_number}"
    order.payment_status = 'paid'
    order.save()
    print(f"Marked order {order.order_number} as paid (id={order.id}).")
    # Send invoice
    try:
        subject = f'Invoice - {getattr(settings, "SITE_NAME", "Site")} - {order.order_number}'
        _send_order_email(order, 'invoice', subject, order.user.email, request=None)
        print('Triggered _send_order_email for order', order.order_number)
    except Exception as exc:
        logging.getLogger(__name__).exception('Error in simulate_upi_send: %s', exc)
        print('Exception while sending invoice:', exc)
