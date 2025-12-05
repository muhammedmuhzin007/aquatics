import os
import sys

# Ensure project root (the parent of this scripts/ folder) is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fishy_friend_aquatics.settings')
import django
django.setup()

from django.test import Client

client = Client()
from django.contrib.auth import get_user_model

# Create and login a test user so we can view the checkout page as an authenticated customer
User = get_user_model()
username = 'inspect_user'
try:
    user = User.objects.get(username=username)
except User.DoesNotExist:
    user = User.objects.create_user(username=username, password='testpass123', email='inspect@example.com')
    # If the project uses a role field, try to set it to customer (best-effort)
    if hasattr(user, 'role'):
        try:
            user.role = 'customer'
            user.save()
        except Exception:
            pass

client.force_login(user)
from store.models import Category, Breed, Fish, Cart, Coupon
from django.utils import timezone

# Ensure the user has at least one cart item so checkout renders
if not Cart.objects.filter(user=user).exists():
    cat, _ = Category.objects.get_or_create(name='Test Category')
    breed, _ = Breed.objects.get_or_create(name='Test Breed', category=cat)
    fish, _ = Fish.objects.get_or_create(name='Test Fish', category=cat, breed=breed, defaults={'price': 100.00, 'stock_quantity': 10})
    Cart.objects.create(user=user, fish=fish, quantity=1)

# Create a coupon and mark it applied in session so the template shows applied state
now = timezone.now()
coupon_code = 'INSPECT10'
coupon, created = Coupon.objects.get_or_create(code=coupon_code, defaults={
    'discount_percentage': 10,
    'is_active': True,
    'show_in_suggestions': True,
    'valid_from': now - timezone.timedelta(days=1),
    'valid_until': now + timezone.timedelta(days=7),
})
sess = client.session
sess['applied_coupon_code'] = coupon.code
sess.save()

# follow redirects to get final HTML
resp = client.get('/checkout/', follow=True)
print('Status:', resp.status_code, 'Final URL:', resp.request['PATH_INFO'])
html = resp.content.decode('utf-8')
lines = html.splitlines()
start = max(0, 100)
end = min(len(lines), 220)
for i in range(start, end):
    print(f"{i+1}: {lines[i]}")
print('\n--- Length:', len(lines))
# Also print any lines around coupon-suggestion occurrences for verification
for idx, line in enumerate(lines):
    if 'coupon-suggestion' in line or 'INSPECT10' in line or 'Applied' in line:
        lo = max(0, idx-3)
        hi = min(len(lines), idx+4)
        print('\n--- Context around line', idx+1)
        for j in range(lo, hi):
            print(f"{j+1}: {lines[j]}")
