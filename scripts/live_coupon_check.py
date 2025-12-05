"""
Standalone live coupon check script.
Can be executed directly with `python scripts\live_coupon_check.py`.
"""
import os
import django

# Initialize Django when running as a standalone script
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fishy_friend_aquatics.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from store.models import Category, Breed, Fish, Cart, Coupon

print('Starting live coupon check script')
client = Client()

# 1) Anonymous apply
print('\n1) Anonymous apply attempt (guest)')
resp = client.post('/apply-coupon/', {'coupon_code': 'GUESTTEST'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
print('Status:', resp.status_code)
try:
    print('JSON:', resp.json())
except Exception:
    print('Content:', resp.content[:400])

# Check session value
sess = client.session
print('Session applied_coupon_code:', sess.get('applied_coupon_code'))

# 2) Create a user and product, add item to cart, create coupon, then login and apply
print('\n2) Create user, product, coupon, add item to cart, authenticate and apply')
User = get_user_model()
username = 'liveuser'
password = 'testpass123'
User.objects.filter(username=username).delete()
user = User.objects.create_user(username=username, password=password, email='live@test.local', role='customer')

# Ensure product exists
cat, _ = Category.objects.get_or_create(name='LiveCat')
breed, _ = Breed.objects.get_or_create(name='LiveBreed', category=cat)
fish, _ = Fish.objects.get_or_create(name='LiveFish', defaults={
    'category': cat,
    'breed': breed,
    'description': 'Live test fish',
    'price': Decimal('200.00'),
    'stock_quantity': 10,
    'minimum_order_quantity': 1,
    'is_available': True,
})
# Clean existing cart and create
Cart.objects.filter(user=user).delete()
Cart.objects.create(user=user, fish=fish, quantity=1)

# Create coupon
now = timezone.now()
Coupon.objects.filter(code='LIVE10').delete()
Coupon.objects.create(code='LIVE10', discount_percentage=Decimal('10.0'), max_discount_amount=Decimal('1000.00'), min_order_amount=Decimal('0.00'), coupon_type='all', is_active=True, show_in_suggestions=True, valid_from=now - timedelta(days=1), valid_until=now + timedelta(days=7), usage_limit=100, times_used=0, created_by=None)

# Login
logged = client.login(username=username, password=password)
print('Logged in as liveuser:', logged)

# Apply coupon
resp2 = client.post('/apply-coupon/', {'coupon_code': 'LIVE10'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
print('Status:', resp2.status_code)
try:
    print('JSON:', resp2.json())
except Exception:
    print('Content:', resp2.content[:400])

print('\nSession applied_coupon_code after login/apply:', client.session.get('applied_coupon_code'))

print('\nLive coupon check script finished')
