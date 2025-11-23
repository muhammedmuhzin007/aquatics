#!/usr/bin/env python3
"""Send an invoice for the most recent order to a given recipient.

Usage:
  python tools/send_invoice_now.py recipient@example.com

This script sets up Django, finds the latest paid order (or latest order),
generates and attaches the invoice PDF using the project's helper, and sends it.
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fishy_friend_aquatics.settings')
import django
django.setup()

from store.models import Order
from store.views import _send_order_email
from django.conf import settings


def main():
    order = Order.objects.filter(payment_status='paid').order_by('-updated_at').first() or Order.objects.all().order_by('-created_at').first()
    if not order:
        print('No orders found in the database. Create an order first.')
        return 1

    recipient = None
    if len(sys.argv) > 1 and sys.argv[1].strip():
        recipient = sys.argv[1].strip()
    else:
        recipient = order.user.email or getattr(settings, 'DEFAULT_FROM_EMAIL', None)

    if not recipient:
        print('No recipient specified and order has no email. Provide recipient as first arg.')
        return 1

    subject = f'Invoice - {getattr(settings, "SITE_NAME", "Site")} - {order.order_number}'
    try:
        _send_order_email(order, 'invoice', subject, recipient, request=None)
        print(f'Sent invoice for {order.order_number} to {recipient}')
        return 0
    except Exception as exc:
        print('Failed to send invoice:', exc)
        return 2


if __name__ == '__main__':
    sys.exit(main())
