from django.test import Client
from django.contrib.auth import get_user_model
from store.models import ComboOffer, ComboItem, Fish, Category, Breed
from django.db import transaction

User = get_user_model()
username = 'smoke_smoke'
password = 'Password123!'

# Create or get test user
user, created = User.objects.get_or_create(username=username, defaults={'email': 'smoke@example.com'})
if created:
    user.set_password(password)
    user.role = 'customer'
    user.save()
    print('Created test user')
else:
    print('Test user exists')

# Ensure there's at least one fish and combo
combo = ComboOffer.objects.first()
if not combo:
    # Ensure category and breed exist
    cat = Category.objects.first() or Category.objects.create(name='Default')
    br = Breed.objects.first() or Breed.objects.create(name='DefaultBreed', category=cat)
    fish = Fish.objects.create(name='SmokeFish', category=cat, breed=br, description='Placeholder', price=10.00, stock_quantity=10, minimum_order_quantity=1)
    combo = ComboOffer.objects.create(title='Smoke Combo', bundle_price=25.00, is_active=True)
    ComboItem.objects.create(combo=combo, fish=fish, quantity=2)
    print('Created test combo and fish')
else:
    print('Using existing combo:', combo.title)

# Use test client to login and add combo
c = Client()
if not c.login(username=username, password=password):
    print('Login failed for', username)
else:
    print('Logged in as', username)
    resp = c.post(f'/add-combo-to-cart/{combo.id}/', follow=True)
    print('POST add-combo-to-cart status:', resp.status_code)
    cart_resp = c.get('/cart/')
    print('GET cart status:', cart_resp.status_code)
    content = cart_resp.content.decode('utf-8')
    if combo.title in content:
        print('Bundle title found in cart page.')
    elif '/remove-bundle/' in content:
        print('Remove-bundle link found; bundle present.')
    else:
        print('Bundle not found. Cart HTML preview:')
        print(content[:1200])
