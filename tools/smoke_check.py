import os
import sys
import pathlib
import django
import json
import argparse
from decimal import Decimal

# Ensure project root is on sys.path so Django settings package is importable
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Allow overriding the payment provider from the CLI for one-off runs
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--provider', '-p', help='Override payment provider (razorpay|mock)')
args, _ = parser.parse_known_args()
if args.provider:
    os.environ['PAYMENT_PROVIDER'] = args.provider

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fishy_friend_aquatics.settings')
django.setup()

from django.conf import settings as dj_settings

# Determine provider: prefer environment, then Django settings, else default to 'mock'
PROVIDER = os.environ.get('PAYMENT_PROVIDER') or getattr(dj_settings, 'PAYMENT_PROVIDER', 'mock')
PROVIDER = (PROVIDER or 'mock').lower()

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

# If order created, route provider create/verify through the provider endpoints
order_id = None
try:
    data = checkout_resp.json()
    order_id = data.get('order_id')
except Exception:
    pass

if not order_id:
    print('No order_id returned from checkout; skipping provider checks')
else:
    # Route create/verify through the configured provider endpoints
    create_path = f'/payments/{PROVIDER}/create/{order_id}/'
    verify_path = f'/payments/{PROVIDER}/verify/'

    create_resp = client.post(create_path)
    print('create status:', create_resp.status_code)
    try:
        create_json = create_resp.json()
        print('create json:', create_json)
    except Exception:
        print('create text:', create_resp.content.decode('utf-8')[:500])
        create_json = {}

    # Build a generic verify payload using whatever id the provider returned
    pid = (
        create_json.get('payment_intent_id') or
        create_json.get('id') or
        create_json.get('payment_intent') or
        create_json.get('provider_order_id') or
        create_json.get('provider_order') or
        f'mock_pid_{order_id}'
    )
    verify_payload = {'payment_intent_id': pid, 'order_id': order_id}
    verify_resp = client.post(verify_path, json.dumps(verify_payload), content_type='application/json')
    print('verify status:', verify_resp.status_code)
    try:
        print('verify json:', verify_resp.json())
    except Exception:
        print('verify text:', verify_resp.content.decode('utf-8')[:500])
