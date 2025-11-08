"""Download real fish images and assign to Fish records.
Alternative: Uses placeholder.com with fish-themed colors or Pexels API.
For best results, manually upload images via Django admin or use a paid API.
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

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aquafish_store.settings")
django.setup()

from store.models import Fish  # noqa: E402

# Using Lorem Picsum (reliable placeholder service) with random fish-related seed
PICSUM_BASE = "https://picsum.photos/800/600?random={seed}"

# Alternative: Use Pexels API (free, requires API key)
# Sign up at https://www.pexels.com/api/ to get a free API key
PEXELS_API_KEY = None  # Replace with your key if you have one
PEXELS_BASE = "https://api.pexels.com/v1/search?query={query}&per_page=1"

# Fish-specific search terms for better results
FISH_QUERIES = {
    "Red Guppy": "red guppy fish",
    "Blue Guppy": "blue guppy fish",
    "Yellow Guppy": "yellow guppy fish",
    "Dalmatian Molly": "dalmatian molly fish",
    "Black Molly": "black molly fish",
    "Sailfin Molly": "sailfin molly fish",
    "Common Goldfish": "goldfish orange",
    "Fantail Goldfish": "fantail goldfish",
    "Black Moor Goldfish": "black moor goldfish",
    "Standard Koi": "koi fish pond",
    "Butterfly Koi": "butterfly koi fish",
    "Showa Koi": "showa koi fish",
    "Ocellaris Clownfish": "clownfish nemo",
    "Percula Clownfish": "clownfish orange",
    "Blue Tang": "blue tang fish dory",
    "Yellow Tang": "yellow tang fish",
    "Powder Blue Tang": "powder blue tang",
    "Purple Tang": "purple tang fish",
    "Male Betta (Red)": "red betta fish",
    "Male Betta (Blue)": "blue betta fish",
    "Halfmoon Betta": "halfmoon betta fish",
    "Silver Angelfish": "silver angelfish",
    "Marble Angelfish": "marble angelfish",
    "Veil Angelfish": "veil angelfish",
    "Silver Arowana": "silver arowana fish",
    "Golden Arowana": "golden arowana fish",
    "Red Arowana": "red arowana fish",
    "Blue Diamond Discus": "blue diamond discus fish",
    "Pigeon Blood Discus": "pigeon blood discus fish",
    "Golden Discus": "golden discus fish",
}


def download_from_pexels(query: str) -> bytes:
    """Download from Pexels API (requires API key)."""
    if not PEXELS_API_KEY:
        return None
    
    headers = {"Authorization": PEXELS_API_KEY}
    try:
        response = requests.get(
            PEXELS_BASE.format(query=query),
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("photos") and len(data["photos"]) > 0:
                photo_url = data["photos"][0]["src"]["large"]
                img_response = requests.get(photo_url, timeout=10)
                if img_response.status_code == 200:
                    return img_response.content
    except Exception as e:
        print(f"  Pexels API error: {e}")
    return None


def download_placeholder(seed: int) -> bytes:
    """Download from Lorem Picsum (guaranteed to work)."""
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
    
    print("Starting fish image download...")
    if PEXELS_API_KEY:
        print("Using Pexels API for real fish images")
    else:
        print("Using Lorem Picsum placeholders (generic nature images)")
        print("To use real fish images:")
        print("  1. Get a free API key from https://www.pexels.com/api/")
        print("  2. Edit this script and set PEXELS_API_KEY = 'your-key-here'")
        print("  3. Run again")
    print("=" * 60)
    
    for idx, fish in enumerate(Fish.objects.all()):
        query = FISH_QUERIES.get(fish.name, f"{fish.breed.name} fish")
        
        print(f"Processing: {fish.name}")
        
        # Try Pexels first if API key is available
        image_data = None
        if PEXELS_API_KEY:
            print(f"  Searching Pexels for: {query}")
            image_data = download_from_pexels(query)
        
        # Fallback to placeholder
        if not image_data:
            print(f"  Using placeholder image (seed: {idx + 1000})")
            image_data = download_placeholder(idx + 1000)
        
        if image_data:
            filename = f"{fish.name.lower().replace(' ', '_').replace('(', '').replace(')', '')}.jpg"
            fish.image.save(filename, ContentFile(image_data), save=True)
            updated += 1
            print(f"  ✓ Image saved")
        else:
            failed += 1
            print(f"  ✗ Failed to download image")
        
        time.sleep(0.3)
    
    print("=" * 60)
    print(f"Complete! Updated: {updated}, Failed: {failed}")
    print("\nNote: For real fish images, get a Pexels API key (free) and update the script.")


if __name__ == "__main__":
    run()
