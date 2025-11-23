"""Download placeholder images and assign them to Category.image.
Uses Lorem Picsum as a fallback; optionally can be extended to use Pexels.
Run: python scripts/download_category_images.py
"""
import os
import sys
from pathlib import Path
import django
import requests
from io import BytesIO
from django.core.files.base import ContentFile
import time

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fishy_friend_aquatics.settings")
django.setup()

from store.models import Category  # noqa: E402

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


def run():
    updated = 0
    failed = 0
    print("Starting category image download...")
    print("Using Lorem Picsum placeholders for category images")
    print("=" * 60)

    for idx, cat in enumerate(Category.objects.all()):
        print(f"Processing Category: {cat.name}")
        image_data = download_placeholder(idx + 2000)
        if image_data:
            filename = f"category_{cat.id}_{cat.name.lower().replace(' ', '_').replace('/', '_')}.jpg"
            try:
                cat.image.save(filename, ContentFile(image_data), save=True)
                updated += 1
                print(f"  ✓ Image saved for category {cat.name}")
            except Exception as e:
                failed += 1
                print(f"  ✗ Failed to save image for {cat.name}: {e}")
        else:
            failed += 1
            print(f"  ✗ Failed to download image for {cat.name}")
        time.sleep(0.2)

    print("=" * 60)
    print(f"Complete! Updated: {updated}, Failed: {failed}")


if __name__ == "__main__":
    run()
