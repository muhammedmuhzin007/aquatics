"""Backfill placeholder images for any Fish without an image, separate from seed logic."""
import os
import sys
from pathlib import Path
import django
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile
from django.conf import settings

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aquafish_store.settings")
django.setup()

from store.models import Fish  # noqa: E402

PALETTE = [
    (46, 125, 50),    # green
    (25, 118, 210),   # blue
    (2, 119, 189),    # deep blue
    (142, 36, 170),   # purple
    (229, 57, 53),    # red
    (255, 143, 0),    # orange
]


def make_placeholder(name: str) -> bytes:
    W, H = 800, 600
    color = PALETTE[hash(name) % len(PALETTE)]
    img = Image.new("RGB", (W, H), color)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except Exception:
        font = ImageFont.load_default()
    tw, th = draw.textbbox((0, 0), name, font=font)[2:]
    draw.text(((W - tw) // 2, (H - th) // 2), name, fill=(255, 255, 255), font=font)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def run():
    updated = 0
    for fish in Fish.objects.all():
        if not fish.image:
            data = make_placeholder(fish.name)
            filename = f"{fish.name.lower().replace(' ', '_')}.jpg"
            fish.image.save(filename, ContentFile(data), save=True)
            updated += 1
    print(f"Placeholder images assigned: {updated}")


if __name__ == "__main__":
    run()
