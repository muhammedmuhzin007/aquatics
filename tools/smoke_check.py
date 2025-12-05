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

print('Checkout endpoint removed; skipping checkout smoke test.')
