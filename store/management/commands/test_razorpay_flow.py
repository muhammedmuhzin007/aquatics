from django.core.management.base import BaseCommand
from django.conf import settings
from django.urls import reverse
from django.test import Client
import uuid
import hmac
import hashlib
import json
import logging


class Command(BaseCommand):
    help = 'Create a test Order and exercise the Razorpay create -> verify flow locally.'

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        from store.models import CustomUser, Order

        # Get or create a test customer
        user = CustomUser.objects.filter(role='customer').first()
        if not user:
            user = CustomUser.objects.create_user(username='test_customer', email='test@example.com', password='testpass')
            user.role = 'customer'
            user.email_verified = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created test user {user.email}'))

        # Create a minimal order
        order = Order.objects.create(
            user=user,
            order_number=Order.generate_order_number(),
            total_amount=10.00,
            final_amount=10.00,
            status='pending',
            payment_method='upi',
            payment_status='pending',
            shipping_address='Test Address',
            phone_number='9999999999',
        )

        self.stdout.write(self.style.SUCCESS(f'Created order {order.order_number} (id={order.id})'))

        # Try to create a provider order via razorpay if configured, otherwise simulate
        provider_order_id = None
        try:
            if getattr(settings, 'RAZORPAY_KEY_ID', None) and getattr(settings, 'RAZORPAY_KEY_SECRET', None):
                try:
                    import razorpay
                    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                    amount_paise = int(float(order.final_amount) * 100)
                    data = {'amount': amount_paise, 'currency': 'INR', 'receipt': order.order_number, 'payment_capture': 1}
                    rp_order = client.order.create(data=data)
                    provider_order_id = rp_order.get('id')
                    order.provider_order_id = provider_order_id
                    order.save(update_fields=['provider_order_id'])
                    self.stdout.write(self.style.SUCCESS(f'Created Razorpay order id: {provider_order_id}'))
                except Exception as exc:
                    logger.exception('Razorpay order creation failed: %s', exc)
                    self.stdout.write(self.style.WARNING('Razorpay order creation failed, falling back to simulated id'))
            if not provider_order_id:
                provider_order_id = f'test_rp_order_{uuid.uuid4().hex[:10]}'
                order.provider_order_id = provider_order_id
                order.save(update_fields=['provider_order_id'])
                self.stdout.write(self.style.SUCCESS(f'Using simulated provider_order_id: {provider_order_id}'))
        except Exception:
            logger.exception('Error creating provider order')

        # Simulate a payment id and compute signature using key secret (if present)
        payment_id = f'pay_{uuid.uuid4().hex[:12]}'
        secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')
        if secret:
            computed = hmac.new(secret.encode('utf-8'), f"{provider_order_id}|{payment_id}".encode('utf-8'), hashlib.sha256).hexdigest()
            signature = computed
        else:
            # If no secret, simulate a signature (won't verify against SDK)
            signature = hmac.new(b'default', f"{provider_order_id}|{payment_id}".encode('utf-8'), hashlib.sha256).hexdigest()

        payload = {
            'razorpay_payment_id': payment_id,
            'razorpay_order_id': provider_order_id,
            'razorpay_signature': signature,
            'order_id': order.id,
        }

        # Use Django test client to POST to verify endpoint (in-process)
        client = Client()
        url = reverse('verify_razorpay_payment')
        resp = client.post(url, data=json.dumps(payload), content_type='application/json')

        self.stdout.write(f'VERIFY endpoint response: {resp.status_code} {resp.content.decode("utf-8")}')

        # Refresh order from DB
        order.refresh_from_db()
        self.stdout.write(self.style.SUCCESS(f'Order payment_status: {order.payment_status}'))
        self.stdout.write(self.style.SUCCESS(f'Order transaction_id: {order.transaction_id}'))
        self.stdout.write(self.style.SUCCESS('Test flow completed.'))
