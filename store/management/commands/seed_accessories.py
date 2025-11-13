from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
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


class Command(BaseCommand):
    help = "Seed the database with 10 sample accessory items. Safe to run multiple times (idempotent by name)."

    def handle(self, *args, **options):
        created = 0
        with transaction.atomic():
            # Ensure categories exist
            category_objs = {}
            for item in ACCESSORY_DATA:
                cat_name = item.get('category')
                if cat_name:
                    cat_obj, _ = Category.objects.get_or_create(name=cat_name, defaults={'description': f'{cat_name} accessories'})
                    category_objs[cat_name] = cat_obj

            for data in ACCESSORY_DATA:
                name = data['name']
                if Accessory.objects.filter(name=name).exists():
                    continue

                cat = None
                if data.get('category'):
                    cat = category_objs.get(data.get('category'))

                acc = Accessory.objects.create(
                    name=name,
                    description=(data.get('description') or f"{name} - high quality accessory."),
                    category=cat,
                    price=Decimal(str(data.get('price', '0.00'))),
                    stock_quantity=int(data.get('stock', 0)),
                    is_active=True,
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Accessory seeding complete. Created={created}."))
