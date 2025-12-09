import os
import random
from io import BytesIO
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile
from django.db.models import Q
from store.models import CustomUser, Review, Fish
import requests

COMMENTS = [
    "Great quality fish!",
    "Healthy and active.",
    "Fast delivery.",
    "Beautiful colors.",
    "Well packed shipment.",
    "Excellent service.",
    "Good value for money.",
    "Will buy again.",
    "Highly recommended.",
    "Satisfied with purchase.",
]


PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"


def run(count=10):
    # Ensure a few sample customers exist
    users = []
    for i in range(3):
        user, _ = CustomUser.objects.get_or_create(
            username=f"reviewer{i+1}",
            defaults={"email": f"reviewer{i+1}@example.com", "role": "customer"},
        )
        users.append(user)

    fishes = list(Fish.objects.all())
    if not fishes:
        print("No fishes found; seed fishes first.")
        return

    created = 0
    for i in range(count):
        user = random.choice(users)
        fish = random.choice(fishes)
        rating = random.randint(4, 5)
        comment = COMMENTS[i % len(COMMENTS)]
        review = Review.objects.create(
            user=user,
            order=None,
            rating=rating,
            comment=f"{comment} ({fish.name})",
            approved=True,
        )
        attach_real_or_placeholder_image(review, fish)
        created += 1
    print(f"Created {created} reviews.")


def attach_placeholder_image(review: Review, fish: Fish):
    """Create a small placeholder image and attach it to the review."""
    W, H = 640, 360
    color = (25, 118, 210)
    img = Image.new("RGB", (W, H), color)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 32)
    except Exception:
        font = ImageFont.load_default()

    text = f"{fish.name}\n{review.rating}★"
    tw, th = draw.multiline_textbbox((0, 0), text, font=font)[2:]
    draw.multiline_text(((W - tw) // 2, (H - th) // 2), text, fill=(255, 255, 255), font=font, align="center")

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    filename = f"review_{review.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.jpg"
    review.image.save(filename, ContentFile(buf.getvalue()), save=True)


def attach_real_or_placeholder_image(review: Review, fish: Fish):
    """Prefer a real image via Pexels; fall back to placeholder if unavailable."""
    if PEXELS_API_KEY:
        img_bytes = fetch_pexels_image(fish.name or fish.breed.name or "aquarium fish")
        if img_bytes:
            filename = f"review_{review.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.jpg"
            review.image.save(filename, ContentFile(img_bytes), save=True)
            return
    # fallback
    attach_placeholder_image(review, fish)


def fetch_pexels_image(query: str):
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": query, "per_page": 1}
    try:
        resp = requests.get(PEXELS_SEARCH_URL, headers=headers, params=params, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
        photos = data.get("photos") or []
        if not photos:
            return None
        photo_url = photos[0].get("src", {}).get("large") or photos[0].get("src", {}).get("medium")
        if not photo_url:
            return None
        img_resp = requests.get(photo_url, timeout=10)
        if img_resp.status_code == 200:
            return img_resp.content
    except Exception:
        return None
    return None


def backfill_images_for_existing():
    """Attach images to existing reviews missing one."""
    reviews = Review.objects.filter(Q(image__isnull=True) | Q(image=""))
    fishes = list(Fish.objects.all())
    if not fishes:
        print("No fishes found; seed fishes first.")
        return
    updated = 0
    for review in reviews:
        fish = random.choice(fishes)
        attach_real_or_placeholder_image(review, fish)
        updated += 1
    print(f"Backfilled images for {updated} reviews.")
