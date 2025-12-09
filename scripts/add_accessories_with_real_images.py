import os
import sys
from pathlib import Path
from decimal import Decimal
import requests
from django.core.files.base import ContentFile
from django.utils.text import slugify

def add_accessories_with_real_images():
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fishy_friend_aquatics.settings")
    import django
    django.setup()

    from store.models import Accessory, Category, CustomUser

    items = [
        {"name": "Premium Aquarium Filter", "price": Decimal("1499.00"), "stock": 60, "image": "https://images.pexels.com/photos/213399/pexels-photo-213399.jpeg?auto=compress&cs=tinysrgb&w=1200"},
        {"name": "Submersible Heater 200W", "price": Decimal("1199.00"), "stock": 75, "image": "https://images.pexels.com/photos/61129/pexels-photo-61129.jpeg?auto=compress&cs=tinysrgb&w=1200"},
        {"name": "LED Light Bar 24 inch", "price": Decimal("899.00"), "stock": 90, "image": "https://images.pexels.com/photos/847393/pexels-photo-847393.jpeg?auto=compress&cs=tinysrgb&w=1200"},
        {"name": "Quiet Air Pump Duo", "price": Decimal("699.00"), "stock": 80, "image": "https://images.pexels.com/photos/1462935/pexels-photo-1462935.jpeg?auto=compress&cs=tinysrgb&w=1200"},
        {"name": "Natural River Gravel 5kg", "price": Decimal("499.00"), "stock": 120, "image": "https://images.pexels.com/photos/1068549/pexels-photo-1068549.jpeg?auto=compress&cs=tinysrgb&w=1200"},
        {"name": "Fine Mesh Fish Net", "price": Decimal("249.00"), "stock": 150, "image": "https://images.pexels.com/photos/1526430/pexels-photo-1526430.jpeg?auto=compress&cs=tinysrgb&w=1200"},
        {"name": "Water Conditioner Pro", "price": Decimal("349.00"), "stock": 140, "image": "https://images.pexels.com/photos/128756/pexels-photo-128756.jpeg?auto=compress&cs=tinysrgb&w=1200"},
        {"name": "Premium Fish Food Mix", "price": Decimal("299.00"), "stock": 200, "image": "https://images.pexels.com/photos/1298682/pexels-photo-1298682.jpeg?auto=compress&cs=tinysrgb&w=1200"},
        {"name": "Master Test Kit", "price": Decimal("899.00"), "stock": 65, "image": "https://images.pexels.com/photos/1287560/pexels-photo-1287560.jpeg?auto=compress&cs=tinysrgb&w=1200"},
        {"name": "Ceramic Cave Decor", "price": Decimal("599.00"), "stock": 85, "image": "https://images.pexels.com/photos/339663/pexels-photo-339663.jpeg?auto=compress&cs=tinysrgb&w=1200"},
    ]

    category, _ = Category.objects.get_or_create(
        name="Aquarium Essentials",
        defaults={"description": "Core accessories for healthy aquariums"},
    )
    creator = CustomUser.objects.filter(role__in=["staff", "admin"]).first()

    created = 0
    for order, item in enumerate(items, start=1):
        acc, is_new = Accessory.objects.get_or_create(
            name=item["name"],
            defaults={
                "category": category,
                "price": item["price"],
                "stock_quantity": item["stock"],
                "minimum_order_quantity": 1,
                "is_active": True,
                "display_order": order,
                "description": f"{item['name']} for everyday tank care.",
                "created_by": creator,
            },
        )

        # If it already existed, refresh core fields but keep existing image if present
        if not is_new:
            acc.category = category
            acc.price = item["price"]
            acc.stock_quantity = item["stock"]
            acc.minimum_order_quantity = 1
            acc.is_active = True
            acc.display_order = order
            acc.description = f"{item['name']} for everyday tank care."
            acc.created_by = acc.created_by or creator
            acc.save()

        if not acc.image:
            try:
                resp = requests.get(item["image"], timeout=15)
                resp.raise_for_status()
                filename = f"{slugify(item['name'])}.jpg"
                acc.image.save(filename, ContentFile(resp.content), save=True)
            except Exception as exc:
                print(f"[warn] Could not download image for {item['name']}: {exc}")
        created += 1 if is_new else 0
        print(f"{'Created' if is_new else 'Updated'}: {acc.name} (id={acc.id})")

    print(f"Done. Accessories created: {created}, total now: {Accessory.objects.count()}")


if __name__ == "__main__":
    add_accessories_with_real_images()
