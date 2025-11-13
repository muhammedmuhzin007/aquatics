"""
Replace or assign an accessory image from a file on disk.

Usage (from project root or inner project dir):

# Use accessory id
python scripts/replace_accessory_image.py --src "C:\path\to\image.jpg" --id 8

# Or use accessory name
python scripts/replace_accessory_image.py --src "C:\path\to\image.jpg" --name "LED Aquarium Light"

This script will copy the source image into MEDIA_ROOT/accessories/ with a safe filename
and set Accessory.image to that relative path.
"""
from pathlib import Path
import argparse
import shutil
import sys
import os

# Ensure project package is on sys.path when called from workspace root
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fishy_friend_aquatics.settings')
import django
django.setup()

from django.conf import settings
from store.models import Accessory

parser = argparse.ArgumentParser(description='Assign an image file to an Accessory')
parser.add_argument('--src', required=True, help='Path to source image file (absolute or relative to current working directory)')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--id', type=int, help='Accessory ID to update')
group.add_argument('--name', help='Accessory name to match (exact match)')
args = parser.parse_args()

src = Path(args.src).expanduser().resolve()
if not src.exists():
    print(f"Source file not found: {src}")
    sys.exit(2)

# Determine accessory
try:
    if args.id:
        accessory = Accessory.objects.get(id=args.id)
    else:
        accessory = Accessory.objects.get(name=args.name)
except Accessory.DoesNotExist:
    print('Accessory not found')
    sys.exit(3)

# Prepare destination
media_root = Path(getattr(settings, 'MEDIA_ROOT', ''))
if not media_root:
    print('MEDIA_ROOT is not configured in settings')
    sys.exit(4)

dest_dir = media_root / 'accessories'
dest_dir.mkdir(parents=True, exist_ok=True)

# Create a safe filename
original_name = src.name
safe_name = f"{accessory.id}_{original_name}"
dest_path = dest_dir / safe_name

# Copy file
shutil.copy2(src, dest_path)

# Assign to accessory (Django ImageField stores relative path from MEDIA_ROOT)
accessory.image = f'accessories/{safe_name}'
accessory.save()

print(f"Assigned {dest_path} to accessory {accessory.id} - {accessory.name}")