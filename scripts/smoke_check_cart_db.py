from django.contrib.auth import get_user_model
from store.models import Cart
User = get_user_model()

u = User.objects.filter(username='smoke_smoke').first()
if not u:
    print('No test user found')
else:
    items = Cart.objects.filter(user=u)
    print('Cart items count:', items.count())
    for it in items:
        print('Cart id:', it.id, 'Fish:', it.fish.name, 'Qty:', it.quantity, 'Combo id:', it.combo_id)
