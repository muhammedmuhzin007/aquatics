"""Razorpay provider adapter.

This adapter uses the official `razorpay` Python package. It creates
Razorpay orders (server-side) and verifies payments and webhooks.
Configuration keys expected in Django settings:
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`
- `RAZORPAY_WEBHOOK_SECRET` (optional, used to validate webhooks)

If the `razorpay` package is not installed the adapter raises
meaningful errors when used.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class RazorpayProvider:
    def __init__(self):
        try:
            import razorpay
            self.razorpay = razorpay
            key_id = getattr(settings, 'RAZORPAY_KEY_ID', '')
            key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')
            self.client = razorpay.Client(auth=(key_id, key_secret))
            # store key id for client-side usage
            self.key_id = key_id
        except Exception:
            self.razorpay = None
            self.client = None
            self.key_id = ''
            logger.exception('razorpay package not installed or configuration missing')

    def create_order(self, order):
        """Create a Razorpay order for `order`.

        Returns a dict with `razorpay_order_id`, `razorpay_key_id`, `amount`, `currency`.
        """
        if not self.client:
            raise Exception('Razorpay SDK not available')

        amount_paise = int(float(order.final_amount or 0) * 100)
        try:
            payload = {
                'amount': amount_paise,
                'currency': 'INR',
                'receipt': str(order.order_number),
                'payment_capture': 1,
            }
            r_order = self.client.order.create(payload)
            return {
                'razorpay_order_id': r_order.get('id'),
                'razorpay_key_id': self.key_id,
                'amount': amount_paise,
                'currency': 'INR',
                'provider_response': r_order,
            }
        except Exception:
            logger.exception('Failed to create razorpay order')
            raise

    def verify_payment(self, data):
        """Verify a Razorpay payment signature.

        Expects `razorpay_payment_id`, `razorpay_order_id`, and `razorpay_signature` in `data`.
        Returns True if signature verifies, False otherwise.
        """
        if not self.razorpay:
            raise Exception('Razorpay SDK not available')

        payment_id = data.get('razorpay_payment_id')
        order_id = data.get('razorpay_order_id')
        signature = data.get('razorpay_signature')
        if not payment_id or not order_id or not signature:
            return False
        try:
            self.client.utility.verify_payment_signature({
                'razorpay_payment_id': payment_id,
                'razorpay_order_id': order_id,
                'razorpay_signature': signature,
            })
            return True
        except Exception:
            logger.exception('Razorpay signature verification failed')
            return False

    def handle_webhook(self, request):
        """Verify Razorpay webhook signature and return (ok, event_or_message).

        Uses `RAZORPAY_WEBHOOK_SECRET` from settings if provided.
        """
        if not self.razorpay:
            return False, 'razorpay sdk missing'
        try:
            body = request.body.decode('utf-8')
        except Exception:
            body = ''
        sig = request.META.get('HTTP_X_RAZORPAY_SIGNATURE')
        secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '')
        if not sig or not secret:
            return False, 'missing signature or webhook secret'
        try:
            self.client.utility.verify_webhook_signature(body, sig, secret)
            import json
            event = json.loads(body) if body else {}
            return True, event
        except Exception:
            logger.exception('Invalid razorpay webhook')
            return False, 'invalid webhook'
