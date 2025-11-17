import os
import sys
import pathlib
import django
import json
from decimal import Decimal

# Ensure project root is on sys.path so Django settings package is importable
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fishy_friend_aquatics.settings')
# Use mock payment provider for local smoke tests
os.environ.setdefault('PAYMENT_PROVIDER', 'mock')
django.setup()

# Ensure Django settings use the mock provider (some setups read from env early;
# setting it explicitly on the settings object guarantees mock provider is used)
from django.conf import settings as dj_settings
try:
    dj_settings.PAYMENT_PROVIDER = 'mock'
except Exception:
    pass

from django.contrib.auth import get_user_model
from django.test import Client
from store.models import Category, Breed, Fish, Cart, Order

User = get_user_model()

USERNAME = 'smoketest'
PASSWORD = 'testpass123'

# Cleanup existing test user
User.objects.filter(username=USERNAME).delete()

# Create test user
user = User(username=USERNAME, email='smoke@example.com', role='customer', is_active=True)
user.set_password(PASSWORD)
user.save()

# Ensure category and breed exist
cat, _ = Category.objects.get_or_create(name='SmokeCat')
breed, _ = Breed.objects.get_or_create(name='SmokeBreed', category=cat)

# Create a fish product
fish, _ = Fish.objects.get_or_create(name='SmokeFish', defaults={
    'category': cat,
    'breed': breed,
    'description': 'Smoke test fish',
    'price': Decimal('99.99'),
    'stock_quantity': 10,
    'minimum_order_quantity': 1,
    'is_available': True,
})
# If fish existed but missing category/breed, ensure they're set
if fish.category_id != cat.id or fish.breed_id != breed.id:
    fish.category = cat
    fish.breed = breed
    fish.save()

# Clear any existing cart for user
Cart.objects.filter(user=user).delete()
# Add cart item
Cart.objects.create(user=user, fish=fish, quantity=1)

client = Client()
logged = client.login(username=USERNAME, password=PASSWORD)
print('Logged in:', logged)

# POST to /checkout/ as AJAX
checkout_data = {
    'shipping_address': '123 Smoke St',
    'phone_number': '9999999999',
    'payment_method': 'card',
}
checkout_resp = client.post('/checkout/', checkout_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
print('checkout status:', checkout_resp.status_code)
try:
    print('checkout json:', checkout_resp.json())
except Exception:
    print('checkout text:', checkout_resp.content.decode('utf-8')[:500])

# If order created, try to call create_razorpay_order
order_id = None
try:
    data = checkout_resp.json()
    order_id = data.get('order_id')
except Exception:
    pass

if order_id:
    create_resp = client.post(f'/payments/razorpay/create/{order_id}/')
    print('create_razorpay status:', create_resp.status_code)
    try:
        print('create_razorpay json:', create_resp.json())
    except Exception:
        print('create_razorpay text:', create_resp.content.decode('utf-8')[:500])

    # Attempt verify with dummy payload (likely to fail if signature doesn't match)
    verify_payload = {
        'razorpay_payment_id': 'pay_ABC',
        'razorpay_order_id': 'order_ABC',
        'razorpay_signature': 'sig_ABC',
        'order_id': order_id,
    }
    verify_resp = client.post('/payments/razorpay/verify/', json.dumps(verify_payload), content_type='application/json')
    print('verify status:', verify_resp.status_code)
    try:
        print('verify json:', verify_resp.json())
    except Exception:
        print('verify text:', verify_resp.content.decode('utf-8')[:500])
else:
    print('No order_id returned from checkout; skipping provider checks')
