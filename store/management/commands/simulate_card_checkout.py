from django.core.management.base import BaseCommand
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.utils import timezone
from store import views, razorpay_integration
from store.models import Fish, Cart
import json


class Command(BaseCommand):
    help = 'Simulate a customer checkout flow using card payment and call provider create endpoint'

    def handle(self, *args, **options):
        User = get_user_model()
        rf = RequestFactory()

        user = User.objects.filter(role='customer').first()
        if not user:
            # create a test customer
            user = User.objects.create(username='e2e_customer', email='e2e@example.com', role='customer', is_active=True)
            user.set_password('password')
            user.save()

        # Ensure there's at least one fish and a cart item
        fish = Fish.objects.filter(is_available=True).first()
        if not fish:
            self.stdout.write(self.style.ERROR('No Fish found in DB to add to cart.'))
            return

        Cart.objects.filter(user=user).delete()
        Cart.objects.create(user=user, fish=fish, quantity=1)

        # Build POST request to checkout (AJAX)
        post_data = {
            'shipping_address': 'Test Address',
            'phone_number': '9999999999',
            'payment_method': 'card',
            'csrfmiddlewaretoken': 'dummy',
        }

        req = rf.post('/checkout/', data=post_data, REMOTE_ADDR='127.0.0.1')
        req.user = user
        # mark as AJAX
        req.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'

        # Instead of calling the CSRF-protected checkout_view, create a draft order
        from store.models import Order, OrderItem
        total = float(fish.price) * 1
        order = Order.objects.create(
            user=user,
            order_number=Order.generate_order_number(),
            total_amount=total,
            final_amount=total,
            shipping_address=post_data['shipping_address'],
            phone_number=post_data['phone_number'],
            payment_method='card',
            payment_status='pending',
        )
        OrderItem.objects.create(order=order, fish=fish, quantity=1, price=fish.price)
        order_id = order.id
        self.stdout.write('Created draft order id=%s (DB-created)' % order_id)

        # Call provider create endpoint
        create_req = rf.post(f'/payments/razorpay/create/{order_id}/')
        create_req.user = user
        create_req.META['REMOTE_ADDR'] = '127.0.0.1'
        self.stdout.write('Calling create_razorpay_payment...')
        create_resp = razorpay_integration.create_razorpay_payment(create_req, order_id=order_id)
        try:
            self.stdout.write('create_razorpay_payment status: %s' % getattr(create_resp, 'status_code', 'N/A'))
            self.stdout.write('create_razorpay_payment content: %s' % create_resp.content.decode('utf-8'))
        except Exception:
            self.stdout.write(self.style.ERROR('Failed to read create_razorpay_payment response'))
