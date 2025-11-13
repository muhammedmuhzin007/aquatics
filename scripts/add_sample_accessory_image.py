"""
Create a small sample accessory image file in MEDIA_ROOT and assign it to the first Accessory record (or create a sample accessory if none exists).
Run with: python scripts/add_sample_accessory_image.py
"""
import os
import django
import base64
import sys
from pathlib import Path

# Ensure project package is importable when running this script from any cwd
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fishy_friend_aquatics.settings')
django.setup()

from django.conf import settings
from store.models import Accessory

# 1x1 transparent PNG
png_b64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
)

media_root = getattr(settings, 'MEDIA_ROOT', None)
if not media_root:
    raise RuntimeError('MEDIA_ROOT is not configured')

accessories_dir = os.path.join(media_root, 'accessories')
os.makedirs(accessories_dir, exist_ok=True)

filename = 'sample_accessory.png'
file_path = os.path.join(accessories_dir, filename)

with open(file_path, 'wb') as f:
    f.write(base64.b64decode(png_b64))

# Assign to an existing accessory or create one
acc = Accessory.objects.first()
if acc:
    acc.image = f'accessories/{filename}'
    acc.save()
    print(f"Assigned image to existing accessory: {acc.id} - {acc.name}")
else:
    acc = Accessory.objects.create(
        name='Sample Accessory',
        description='Automatically added sample accessory',
        price=49.99,
        stock_quantity=10,
        minimum_order_quantity=1,
        image=f'accessories/{filename}',
        is_active=True
    )
    print(f"Created accessory with image: {acc.id} - {acc.name}")

print('Wrote file:', file_path)