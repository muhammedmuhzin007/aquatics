import os
import django
import sys
from decimal import Decimal

# setup
proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fishy_friend_aquatics.settings')
django.setup()

from store.models import Category, Accessory

ACCESSORY_DATA = [
    {"name": "Bio-Filter 100", "category": "Filters", "price": "999.00", "stock": 25},
    {"name": "Aqua Net XL", "category": "Nets", "price": "299.00", "stock": 50},
    {"name": "Premium Fish Food 1kg", "category": "Food", "price": "499.00", "stock": 120},
    {"name": "Heater 200W", "category": "Equipment", "price": "1299.00", "stock": 30},
    {"name": "CO2 Diffuser", "category": "Plants", "price": "699.00", "stock": 40},
    {"name": "pH Test Kit", "category": "Test Kits", "price": "249.00", "stock": 80},
    {"name": "Gravel Vacuum", "category": "Maintenance", "price": "349.00", "stock": 45},
    {"name": "LED Aquarium Light", "category": "Lighting", "price": "1599.00", "stock": 20},
    {"name": "Decorative Rock Set", "category": "Decor", "price": "199.00", "stock": 60},
    {"name": "Water Conditioner 500ml", "category": "Chemicals", "price": "179.00", "stock": 150},
]

created = 0
for item in ACCESSORY_DATA:
    name = item['name']
    if Accessory.objects.filter(name=name).exists():
        continue
    cat = None
    if item.get('category'):
        cat, _ = Category.objects.get_or_create(name=item['category'], defaults={'description': f"{item['category']} accessories"})
    acc = Accessory.objects.create(
        name=name,
        description=f"{name} - high quality accessory.",
        category=cat,
        price=Decimal(str(item['price'])),
        stock_quantity=int(item['stock']),
        is_active=True,
    )
    created += 1

print(f"Created {created} accessories")
print(f"Total accessories now: {Accessory.objects.count()}")
