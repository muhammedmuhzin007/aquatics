from django.core.management.base import BaseCommand
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.utils import timezone
import json
import logging

from store import razorpay_integration
from store.payments.mock import MockProvider
from store.models import Order

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run a simulated end-to-end payment flow using the MockProvider (local tests)'

    def handle(self, *args, **options):
        rf = RequestFactory()

        User = get_user_model()
        user, _ = User.objects.get_or_create(username='e2e_test_user', defaults={'email': 'e2e@example.com'})

        # Create a draft order
        order = Order.objects.create(
            user=user,
            order_number=Order.generate_order_number(),
            total_amount=100.00,
            final_amount=100.00,
            payment_status='pending',
        )

        self.stdout.write(self.style.SUCCESS(f'Created test order id={order.id} order_number={order.order_number}'))

        # Monkeypatch get_payment_provider in the razorpay_integration module to return a mock that
        # responds with a sensible create_order and verify behavior.
        class LocalMock(MockProvider):
            def handle_webhook(self, request):
                try:
                    body = request.body.decode('utf-8')
                    event = json.loads(body)
                    return True, event
                except Exception:
                    return True, {}

        orig_get = razorpay_integration.get_payment_provider
        try:
            razorpay_integration.get_payment_provider = lambda name=None: LocalMock()

            # Call create_razorpay_payment view
            req = rf.post(f'/payments/razorpay/create/{order.id}/')
            resp = razorpay_integration.create_razorpay_payment(req, order.id)
            content = getattr(resp, 'content', b'').decode('utf-8')
            self.stdout.write('Create response:')
            self.stdout.write(content)

            # Simulate the client-side success payload (mock values)
            payload = {
                'razorpay_payment_id': f'mock_pay_{order.id}',
                'razorpay_order_id': f'mock_order_{order.id}',
                'razorpay_signature': 'mocksig',
                'order_id': order.id,
            }

            vreq = rf.post('/payments/razorpay/verify/', data=json.dumps(payload), content_type='application/json')
            vresp = razorpay_integration.verify_razorpay_payment(vreq)
            self.stdout.write('Verify response:')
            try:
                self.stdout.write(vresp.content.decode('utf-8'))
            except Exception:
                self.stdout.write(str(vresp))

            # Refresh order from DB
            order.refresh_from_db()
            self.stdout.write(self.style.SUCCESS(f'Order after verify: payment_status={order.payment_status} transaction_id={order.transaction_id} provider_order_id={order.provider_order_id}'))

            # Simulate webhook: payment.captured
            event = {
                'event': 'payment.captured',
                'payload': {
                    'payment': {
                        'entity': {
                            'id': f'mock_pay_{order.id}',
                            'order_id': f'mock_order_{order.id}',
                            'amount': int(float(order.final_amount) * 100),
                        }
                    }
                }
            }
            wreq = rf.post('/payments/razorpay/webhook/', data=json.dumps(event), content_type='application/json', **{'HTTP_X_RAZORPAY_SIGNATURE': 'mocksig'})
            wresp = razorpay_integration.razorpay_webhook(wreq)
            self.stdout.write('Webhook response status: %s' % getattr(wresp, 'status_code', str(wresp)))

            order.refresh_from_db()
            self.stdout.write(self.style.SUCCESS(f'Order after webhook: payment_status={order.payment_status} transaction_id={order.transaction_id} provider_order_id={order.provider_order_id}'))

        finally:
            razorpay_integration.get_payment_provider = orig_get

        self.stdout.write(self.style.SUCCESS('E2E payment simulation complete.'))
