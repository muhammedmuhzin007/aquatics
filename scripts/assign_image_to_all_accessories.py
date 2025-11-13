"""
Assign a single image file to every Accessory in the database.

Usage examples:
# Use an existing file in the workspace/media
python scripts/assign_image_to_all_accessories.py --src "media/accessories/sample_accessory.png"

# Use an absolute file path from your machine
python scripts/assign_image_to_all_accessories.py --src "C:\path\to\image.jpg"

If --src is omitted, the script will attempt to use 'media/accessories/sample_accessory.png'.
The script copies the src image for each accessory (names them accessory_<id>_origname.ext) and assigns it.
"""
from pathlib import Path
import argparse
import shutil
import sys
import os

# Ensure project package is on sys.path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fishy_friend_aquatics.settings')
import django
django.setup()

from django.conf import settings
from store.models import Accessory

parser = argparse.ArgumentParser(description='Assign an image file to every Accessory')
parser.add_argument('--src', help='Path to source image file (default: media/accessories/sample_accessory.png)')
args = parser.parse_args()

if args.src:
    src = Path(args.src).expanduser().resolve()
else:
    src = (project_root / 'media' / 'accessories' / 'sample_accessory.png').resolve()

if not src.exists():
    print(f"Source file not found: {src}")
    sys.exit(2)

media_root = Path(getattr(settings, 'MEDIA_ROOT', ''))
if not media_root:
    print('MEDIA_ROOT is not configured in settings')
    sys.exit(3)

dest_dir = media_root / 'accessories'
dest_dir.mkdir(parents=True, exist_ok=True)

accessories = list(Accessory.objects.all())
if not accessories:
    print('No accessories found in database.')
    sys.exit(0)

for acc in accessories:
    safe_name = f"{acc.id}_{src.name}"
    dest_path = dest_dir / safe_name
    shutil.copy2(src, dest_path)
    acc.image = f'accessories/{safe_name}'
    acc.save()
    print(f"Assigned image to accessory {acc.id} - {acc.name} -> {dest_path}")

print('Done: assigned images to', len(accessories), 'accessories.')
