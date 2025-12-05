from django.test import Client
from django.contrib.auth import get_user_model
from store.models import ComboOffer

User = get_user_model()
username='smoke_smoke'
password='Password123!'

c = Client()
if not c.login(username=username, password=password):
    print('Login failed')
else:
    resp = c.get('/cart/')
    content = resp.content.decode('utf-8')
    combo = ComboOffer.objects.first()
    print('Status', resp.status_code)
    print('Has bundle-row?', 'bundle-row' in content)
    print('Has remove-bundle?', '/remove-bundle/' in content)
    if combo:
        print('Combo title present?', combo.title in content)
    print('Content length:', len(content))
    # Optionally write to file
    open('temp_cart.html','w', encoding='utf-8').write(content)
    print('Wrote temp_cart.html')
