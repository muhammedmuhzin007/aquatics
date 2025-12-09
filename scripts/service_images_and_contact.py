"""Assign placeholder images to Service.image and create/update ContactInfo.
Run: python scripts/service_images_and_contact.py
"""
import os
import sys
from pathlib import Path
import django
import requests
from django.core.files.base import ContentFile
import time

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fishy_friend_aquatics.settings")
django.setup()

from store.models import Service, ContactInfo  # noqa: E402

PICSUM_BASE = "https://picsum.photos/800/600?random={seed}"


def download_placeholder(seed: int) -> bytes:
    url = PICSUM_BASE.format(seed=seed)
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        if response.status_code == 200 and response.content:
            return response.content
    except Exception as e:
        print(f"  Failed to download placeholder: {e}")
    return None


def assign_service_images():
    updated = 0
    failed = 0
    services = Service.objects.all()
    print(f"Found {services.count()} services. Assigning images where missing...")
    for idx, svc in enumerate(services):
        if svc.image:
            continue
        image_data = download_placeholder(3000 + idx)
        if image_data:
            filename = f"service_{svc.id}_{svc.title.lower().replace(' ', '_')}.jpg"
            try:
                svc.image.save(filename, ContentFile(image_data), save=True)
                updated += 1
                print(f"  ✓ Image saved for service: {svc.title}")
            except Exception as e:
                failed += 1
                print(f"  ✗ Failed to save image for {svc.title}: {e}")
        else:
            failed += 1
            print(f"  ✗ Failed to download image for {svc.title}")
        time.sleep(0.2)

    print(f"Service images: updated={updated}, failed={failed}")


def create_or_update_contact():
    # Sample contact details - update as needed
    details = {
        'address_line1': 'FISHY FRIEND AQUA, 123 Ocean Avenue',
        'address_line2': 'Suite 5B',
        'city': 'Mumbai',
        'state': 'Maharashtra',
        'postal_code': '400001',
        'country': 'India',
        'phone_primary': '+91 98765 43210',
        'phone_secondary': '+91 91234 56789',
        'email_support': 'support@fishyfriend.com',
        'email_sales': 'sales@fishyfriend.com',
        'whatsapp': '+919876543210',
        'facebook_url': 'https://facebook.com/fishyfriend',
        'instagram_url': 'https://instagram.com/fishyfriend',
        'twitter_url': '',
        'youtube_url': '',
        'map_embed_url': '',
        'opening_hours': 'Mon-Fri: 09:00 - 18:00\nSat: 10:00 - 16:00\nSun: Closed',
    }

    ci = ContactInfo.objects.first()
    if not ci:
        ci = ContactInfo.objects.create(**details)
        print("Created ContactInfo record.")
    else:
        for k, v in details.items():
            setattr(ci, k, v)
        ci.save()
        print("Updated existing ContactInfo record.")


if __name__ == '__main__':
    assign_service_images()
    create_or_update_contact()
