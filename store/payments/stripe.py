"""Stripe payment provider adapter.

This is a minimal adapter that creates PaymentIntents and verifies them.
It prefers the `stripe` package but fails gracefully if it's missing.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class StripeProvider:
    def __init__(self):
        try:
            import stripe
            self.stripe = stripe
            self.stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
        except Exception:
            self.stripe = None
            logger.exception('stripe package not installed or configuration missing')

    def create_order(self, order):
        """Create a Stripe PaymentIntent for the given Order.

        Returns a dict containing `payment_intent_id`, `client_secret`, and
        the publishable key for client-side usage.
        """
        if not self.stripe:
            raise Exception('Stripe SDK not available')

        amount_paise = int(float(order.final_amount or 0) * 100)
        try:
            intent = self.stripe.PaymentIntent.create(
                amount=amount_paise,
                currency='inr',
                metadata={'order_id': str(order.id), 'order_number': order.order_number},
                description=f'Order {order.order_number}',
            )
            return {
                'payment_intent_id': intent.id,
                'client_secret': intent.client_secret,
                'stripe_publishable_key': getattr(settings, 'STRIPE_PUBLISHABLE_KEY', ''),
                'amount': amount_paise,
                'currency': 'INR',
            }
        except Exception:
            logger.exception('Failed to create Stripe PaymentIntent')
            raise

    def verify_payment(self, data):
        """Verify a Stripe PaymentIntent by retrieving it and checking status.

        Expects `payment_intent_id` in `data`.
        """
        if not self.stripe:
            raise Exception('Stripe SDK not available')

        pid = data.get('payment_intent_id')
        if not pid:
            return False
        try:
            intent = self.stripe.PaymentIntent.retrieve(pid)
            return intent.status == 'succeeded'
        except Exception:
            logger.exception('Failed to retrieve Stripe PaymentIntent %s', pid)
            return False

    def handle_webhook(self, request):
        """Verify Stripe webhook signature and return (ok, event) tuple.

        Uses `STRIPE_WEBHOOK_SECRET` configured in settings.
        """
        if not self.stripe:
            return False, 'stripe sdk missing'
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
        if not sig_header or not secret:
            return False, 'missing signature or secret'
        try:
            event = self.stripe.Webhook.construct_event(payload, sig_header, secret)
            return True, event
        except Exception:
            logger.exception('Invalid stripe webhook')
            return False, 'invalid webhook'
