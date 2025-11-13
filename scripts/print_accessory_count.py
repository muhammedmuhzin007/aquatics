import os
import django
import sys

# ensure project root is in path
proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fishy_friend_aquatics.settings')
django.setup()

from store.models import Accessory

print(Accessory.objects.count())
print('\n-- list --')
for a in Accessory.objects.all():
    print(a.name, a.price, a.stock_quantity)
