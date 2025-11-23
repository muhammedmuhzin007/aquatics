import os
import random
from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings

from store.models import Accessory, Category, CustomUser


SAMPLE_IMAGES = [
    'static/images/image.png',
    'static/images/image1.png',
    'static/images/hero-betta-fish.png',
    'static/images/underwater.jpg',
    'static/images/logo.jpg',
]


class Command(BaseCommand):
    help = 'Create 20 Accessory records and attach sample images from static/images'

    def handle(self, *args, **options):
        base_dir = settings.BASE_DIR
        media_dir = os.path.join(base_dir, 'media', 'accessories')
        os.makedirs(media_dir, exist_ok=True)

        # pick or create a default category
        cat, _ = Category.objects.get_or_create(name='General Accessories', defaults={'description': 'Default accessories'})

        creator = CustomUser.objects.filter(role__in=['staff', 'admin']).first()

        created = 0
        for i in range(1, 21):
            name = f'Accessory {i}'
            price = round(random.uniform(99.0, 1499.0), 2)
            stock = random.randint(5, 200)
            src = random.choice(SAMPLE_IMAGES)
            src_path = os.path.join(base_dir, src)
            if not os.path.exists(src_path):
                # try static root fallback
                src_path = os.path.join(base_dir, 'static', 'images', os.path.basename(src))
            if not os.path.exists(src_path):
                self.stdout.write(self.style.WARNING(f'Sample image not found: {src}, skipping image for {name}'))

            accessory = Accessory.objects.create(
                name=name,
                description=f'Sample description for {name}',
                category=cat,
                price=price,
                stock_quantity=stock,
                minimum_order_quantity=1,
                is_active=True,
                display_order=i,
                created_by=creator,
            )

            # attach image by saving a copy into accessory.image
            try:
                if os.path.exists(src_path):
                    ext = os.path.splitext(src_path)[1] or '.jpg'
                    dest_filename = f'accessory-{i}{ext}'
                    with open(src_path, 'rb') as f:
                        accessory.image.save(dest_filename, File(f), save=True)
                created += 1
                self.stdout.write(self.style.SUCCESS(f'Created accessory: {accessory.name} (id={accessory.id})'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to attach image for {name}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Total accessories created: {created}'))
