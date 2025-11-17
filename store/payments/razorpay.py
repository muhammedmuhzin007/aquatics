import logging
from django.conf import settings
from .base import BasePaymentProvider

class RazorpayProvider(BasePaymentProvider):
    def __init__(self):
        try:
            import razorpay
            self.client = razorpay.Client(auth=(getattr(settings, 'RAZORPAY_KEY_ID', ''), getattr(settings, 'RAZORPAY_KEY_SECRET', '')))
        except Exception:
            self.client = None
            logging.getLogger(__name__).exception('razorpay package not installed')

    def create_order(self, order):
        if not self.client:
            raise Exception('Razorpay SDK not installed')
        amount_paise = int(float(order.final_amount) * 100)
        data = {
            'amount': amount_paise,
            'currency': 'INR',
            'receipt': order.order_number,
            'payment_capture': 1,
        }
        razor_order = self.client.order.create(data=data)
        return {
            'razorpay_order_id': razor_order.get('id'),
            'razorpay_key': getattr(settings, 'RAZORPAY_KEY_ID', ''),
            'amount': amount_paise,
            'currency': 'INR',
        }

    def verify_payment(self, data):
        try:
            self.client.utility.verify_payment_signature({
                'razorpay_order_id': data['razorpay_order_id'],
                'razorpay_payment_id': data['razorpay_payment_id'],
                'razorpay_signature': data['razorpay_signature'],
            })
            return True
        except Exception:
            return False

    def handle_webhook(self, request):
        import hmac, hashlib, json
        payload = request.body or b''
        signature = request.META.get('HTTP_X_RAZORPAY_SIGNATURE')
        secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '')
        if not signature or not secret:
            return False, 'Missing signature or secret'
        computed = hmac.new(secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(computed, signature):
            return False, 'Invalid signature'
        try:
            event = json.loads(payload.decode('utf-8'))
            return True, event
        except Exception:
            return False, 'Invalid JSON'
