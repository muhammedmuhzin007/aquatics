import os
import sys
from decimal import Decimal
from pathlib import Path
from datetime import timedelta
from django.utils import timezone
import requests
from django.core.files.base import ContentFile


def add_limited_offers():
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fishy_friend_aquatics.settings")
    import django
    django.setup()

    from store.models import LimitedOffer, Fish

    offers = [
        {
            "title": "Weekend Wave Deal",
            "discount_text": "Save 15% on featured fish",
            "days": 7,
            "bg_color": "#0f172a",
            "image_url": "https://images.pexels.com/photos/61129/pexels-photo-61129.jpeg?auto=compress&cs=tinysrgb&w=1200",
        },
        {
            "title": "Midnight Reef Rush",
            "discount_text": "12% off midnight picks",
            "days": 5,
            "bg_color": "#0b253b",
            "image_url": "https://images.pexels.com/photos/847393/pexels-photo-847393.jpeg?auto=compress&cs=tinysrgb&w=1200",
        },
        {
            "title": "Coral Craze",
            "discount_text": "Flat ₹250 on corals",
            "days": 6,
            "bg_color": "#112031",
            "image_url": "https://images.pexels.com/photos/213399/pexels-photo-213399.jpeg?auto=compress&cs=tinysrgb&w=1200",
        },
        {
            "title": "Feeder Frenzy",
            "discount_text": "18% off feeder packs",
            "days": 4,
            "bg_color": "#0f1f2f",
            "image_url": "https://images.pexels.com/photos/1526430/pexels-photo-1526430.jpeg?auto=compress&cs=tinysrgb&w=1200",
        },
        {
            "title": "Starter Tank Special",
            "discount_text": "Save 20% on combos",
            "days": 5,
            "bg_color": "#102a43",
            "image_url": "https://images.pexels.com/photos/1068549/pexels-photo-1068549.jpeg?auto=compress&cs=tinysrgb&w=1200",
        },
    ]

    fishes = list(Fish.objects.filter(is_available=True)[:10])
    if not fishes:
        print("No fishes available to attach offers.")
        return

    now = timezone.now()
    created = 0
    for idx, data in enumerate(offers, start=1):
        fish = fishes[(idx - 1) % len(fishes)]
        start = now + timedelta(hours=idx)
        end = start + timedelta(days=data["days"])
        offer, is_new = LimitedOffer.objects.get_or_create(
            title=data["title"],
            defaults={
                "description": f"Limited offer on {fish.name}. {data['discount_text']}",
                "discount_text": data["discount_text"],
                "start_time": start,
                "end_time": end,
                "is_active": True,
                "show_on_homepage": True,
                "bg_color": data.get("bg_color", "#0f172a"),
            },
        )
        if not is_new:
            # refresh timing/discount and mark active
            offer.discount_text = data["discount_text"]
            offer.start_time = start
            offer.end_time = end
            offer.is_active = True
            offer.show_on_homepage = True
            offer.bg_color = data.get("bg_color", "#0f172a")
            offer.save()
        offer.fish = fish
        # attach image if not present
        if not offer.image and data.get("image_url"):
            try:
                resp = requests.get(data["image_url"], timeout=15)
                resp.raise_for_status()
                filename = f"limited-offer-{idx}.jpg"
                offer.image.save(filename, ContentFile(resp.content), save=True)
            except Exception as exc:
                print(f"[warn] Could not download image for {offer.title}: {exc}")
        offer.save()
        created += 1 if is_new else 0
        print(f"{'Created' if is_new else 'Updated'} offer: {offer.title} -> {fish.name}")

    print(f"Done. Offers created: {created}, total now: {LimitedOffer.objects.count()}")


if __name__ == "__main__":
    add_limited_offers()
