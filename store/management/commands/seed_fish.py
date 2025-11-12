from django.core.management.base import BaseCommand
from django.db import transaction
from django.core.files.base import ContentFile
from store.models import Category, Breed, Fish
from decimal import Decimal
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import random

CATEGORIES = {
    "Tropical": ["Guppy", "Molly"],
    "Freshwater": ["Goldfish", "Koi"],
    "Saltwater": ["Clownfish", "Tang"],
    "Ornamental": ["Betta", "Angelfish"],
    "Rare": ["Arowana", "Discus"],
}

FISH_DATA = [
    # Tropical
    {"name": "Red Guppy", "category": "Tropical", "breed": "Guppy", "size": "small", "price": "3.50", "stock": 120},
    {"name": "Blue Guppy", "category": "Tropical", "breed": "Guppy", "size": "small", "price": "3.75", "stock": 95},
    {"name": "Yellow Guppy", "category": "Tropical", "breed": "Guppy", "size": "small", "price": "3.60", "stock": 110},
    {"name": "Dalmatian Molly", "category": "Tropical", "breed": "Molly", "size": "medium", "price": "4.50", "stock": 80},
    {"name": "Black Molly", "category": "Tropical", "breed": "Molly", "size": "medium", "price": "4.25", "stock": 75},
    {"name": "Sailfin Molly", "category": "Tropical", "breed": "Molly", "size": "medium", "price": "5.00", "stock": 60},
    # Freshwater
    {"name": "Common Goldfish", "category": "Freshwater", "breed": "Goldfish", "size": "medium", "price": "2.50", "stock": 200},
    {"name": "Fantail Goldfish", "category": "Freshwater", "breed": "Goldfish", "size": "medium", "price": "5.50", "stock": 90},
    {"name": "Black Moor Goldfish", "category": "Freshwater", "breed": "Goldfish", "size": "medium", "price": "6.00", "stock": 70},
    {"name": "Standard Koi", "category": "Freshwater", "breed": "Koi", "size": "large", "price": "15.00", "stock": 40},
    {"name": "Butterfly Koi", "category": "Freshwater", "breed": "Koi", "size": "large", "price": "18.00", "stock": 35},
    {"name": "Showa Koi", "category": "Freshwater", "breed": "Koi", "size": "xlarge", "price": "55.00", "stock": 10},
    # Saltwater
    {"name": "Ocellaris Clownfish", "category": "Saltwater", "breed": "Clownfish", "size": "small", "price": "25.00", "stock": 50},
    {"name": "Percula Clownfish", "category": "Saltwater", "breed": "Clownfish", "size": "small", "price": "28.00", "stock": 45},
    {"name": "Blue Tang", "category": "Saltwater", "breed": "Tang", "size": "large", "price": "60.00", "stock": 25},
    {"name": "Yellow Tang", "category": "Saltwater", "breed": "Tang", "size": "large", "price": "58.00", "stock": 30},
    {"name": "Powder Blue Tang", "category": "Saltwater", "breed": "Tang", "size": "large", "price": "75.00", "stock": 15},
    {"name": "Purple Tang", "category": "Saltwater", "breed": "Tang", "size": "large", "price": "68.00", "stock": 18},
    # Ornamental
    {"name": "Male Betta (Red)", "category": "Ornamental", "breed": "Betta", "size": "small", "price": "8.00", "stock": 100},
    {"name": "Male Betta (Blue)", "category": "Ornamental", "breed": "Betta", "size": "small", "price": "8.50", "stock": 95},
    {"name": "Halfmoon Betta", "category": "Ornamental", "breed": "Betta", "size": "small", "price": "12.00", "stock": 60},
    {"name": "Silver Angelfish", "category": "Ornamental", "breed": "Angelfish", "size": "medium", "price": "9.00", "stock": 70},
    {"name": "Marble Angelfish", "category": "Ornamental", "breed": "Angelfish", "size": "medium", "price": "10.00", "stock": 65},
    {"name": "Veil Angelfish", "category": "Ornamental", "breed": "Angelfish", "size": "large", "price": "14.00", "stock": 40},
    # Rare
    {"name": "Silver Arowana", "category": "Rare", "breed": "Arowana", "size": "xlarge", "price": "120.00", "stock": 8},
    {"name": "Golden Arowana", "category": "Rare", "breed": "Arowana", "size": "xlarge", "price": "250.00", "stock": 5},
    {"name": "Red Arowana", "category": "Rare", "breed": "Arowana", "size": "xlarge", "price": "300.00", "stock": 3},
    {"name": "Blue Diamond Discus", "category": "Rare", "breed": "Discus", "size": "large", "price": "85.00", "stock": 12},
    {"name": "Pigeon Blood Discus", "category": "Rare", "breed": "Discus", "size": "large", "price": "90.00", "stock": 10},
    {"name": "Golden Discus", "category": "Rare", "breed": "Discus", "size": "large", "price": "95.00", "stock": 9},
]

DEFAULT_DESCRIPTION = "High-quality healthy specimen. Suitable for both beginners and experienced aquarists."

class Command(BaseCommand):
    help = "Seed the database with sample categories, breeds, and 30 fish records. Safe to run multiple times. Also assigns placeholder images where missing."

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=None,
            help='Total number of fish records to ensure in the database (default: uses built-in list size).',
        )

    def _make_placeholder(self, text: str, category: str) -> bytes:
        """Create a simple placeholder image with the fish name; return image bytes (JPEG)."""
        # Pick a background color based on category for some variety
        palette = {
            "Tropical": (46, 125, 50),       # green
            "Freshwater": (25, 118, 210),    # blue
            "Saltwater": (2, 119, 189),      # deep blue
            "Ornamental": (142, 36, 170),    # purple
            "Rare": (229, 57, 53),           # red
        }
        bg = palette.get(category, (55, 71, 79))

        W, H = 800, 600
        img = Image.new("RGB", (W, H), bg)
        draw = ImageDraw.Draw(img)

        # Try a nicer font; fallback to default if not available
        try:
            # Common Windows fonts path example; Pillow will fallback if missing
            font = ImageFont.truetype("arial.ttf", 44)
        except Exception:
            font = ImageFont.load_default()

        # Wrap text roughly if long
        title = text
        # Compute text size and position
        tw, th = draw.textbbox((0, 0), title, font=font)[2:]
        x = (W - tw) // 2
        y = (H - th) // 2
        draw.text((x, y), title, fill=(255, 255, 255), font=font)

        # Add a subtle watermark-like label
        from django.conf import settings
        sub = getattr(settings, 'SITE_NAME', 'Fishy Friend Aquatics')
        sub_font = font
        try:
            sub_font = ImageFont.truetype("arial.ttf", 24)
        except Exception:
            pass
        sb = draw.textbbox((0, 0), sub, font=sub_font)
        draw.text((W - sb[2] - 20, H - sb[3] - 20), sub, fill=(255, 255, 255), font=sub_font)

        # Convert to bytes
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return buf.getvalue()

    def handle(self, *args, **options):
        created_categories = 0
        created_breeds = 0
        created_fish = 0
        images_assigned = 0

        with transaction.atomic():
            # Ensure categories and breeds
            category_objs = {}
            breed_objs = {}
            for cat_name, breed_list in CATEGORIES.items():
                cat_obj, cat_created = Category.objects.get_or_create(name=cat_name, defaults={"description": f"{cat_name} category"})
                if cat_created:
                    created_categories += 1
                category_objs[cat_name] = cat_obj
                for breed_name in breed_list:
                    breed_obj, breed_created = Breed.objects.get_or_create(name=breed_name, category=cat_obj, defaults={"description": f"{breed_name} breed"})
                    if breed_created:
                        created_breeds += 1
                    breed_objs[(cat_name, breed_name)] = breed_obj

            # Seed fish
            # Determine if a target count was requested
            target_count = options.get('count')
            existing_count = Fish.objects.count()
            base_list = list(FISH_DATA)

            if target_count is None:
                # default: create from provided static list only
                to_create_list = base_list
            else:
                # build a list of fish data up to target_count
                to_create_list = list(base_list)
                # If target_count is larger than base list, generate additional variants
                idx = 1
                while len(to_create_list) + existing_count < target_count:
                    # pick random category and breed
                    cat_name = random.choice(list(CATEGORIES.keys()))
                    breed_name = random.choice(CATEGORIES[cat_name])
                    name = f"{breed_name} Variant {idx}"
                    price = f"{round(random.uniform(2.0, 120.0), 2)}"
                    stock = random.randint(5, 200)
                    size = random.choice(["small", "medium", "large", "xlarge"]) if isinstance(FISH_DATA[0]['size'], str) else round(random.uniform(1.0, 12.0), 2)
                    to_create_list.append({
                        "name": name,
                        "category": cat_name,
                        "breed": breed_name,
                        "size": size,
                        "price": price,
                        "stock": stock,
                    })
                    idx += 1

            for data in to_create_list:
                cat_obj = category_objs[data["category"]]
                breed_obj = breed_objs[(data["category"], data["breed"])]
                # ensure unique name by appending a suffix if necessary
                base_name = data["name"]
                name = base_name
                suffix = 1
                while Fish.objects.filter(name=name, breed=breed_obj).exists():
                    name = f"{base_name} #{suffix}"
                    suffix += 1

                # Normalize size: model expects a decimal (inches). Map common labels to approximate values.
                size_val = data.get("size")
                if isinstance(size_val, str):
                    size_map = {
                        "small": Decimal('2.00'),
                        "medium": Decimal('4.00'),
                        "large": Decimal('8.00'),
                        "xlarge": Decimal('15.00'),
                    }
                    size_norm = size_map.get(size_val.lower(), None)
                else:
                    # numeric already
                    size_norm = size_val

                fish_obj, fish_created = Fish.objects.get_or_create(
                    name=name,
                    breed=breed_obj,
                    defaults={
                        "category": cat_obj,
                        "description": DEFAULT_DESCRIPTION,
                        "price": Decimal(str(data.get("price", "0.00"))),
                        "size": size_norm,
                        "stock_quantity": data.get("stock", 0),
                        "is_available": True,
                    }
                )
                if fish_created:
                    created_fish += 1

                # Assign placeholder image if missing
                if not fish_obj.image:
                    img_bytes = self._make_placeholder(fish_obj.name, fish_obj.category.name)
                    filename = f"{fish_obj.name.lower().replace(' ', '_')}_{random.randint(1000,9999)}.jpg"
                    fish_obj.image.save(filename, ContentFile(img_bytes), save=True)
                    images_assigned += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seeding complete: Categories created={created_categories}, Breeds created={created_breeds}, Fish created={created_fish}, Images assigned={images_assigned}."
        ))
