from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from store.models import Category, Plant


class Command(BaseCommand):
    help = "Seed the database with aquatic plants and associated images."

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (compatible; FishyFriendSeeder/1.0; +https://example.com/seeder)",
        "Referer": "https://commons.wikimedia.org/",
    }

    PLANT_DATA = [
        {
            "name": "Amazon Sword",
            "category": "Background Plants",
            "description": "Classic rosette plant with broad leaves that thrives in nutrient rich substrates and moderate lighting.",
            "price": "499.00",
            "stock": 24,
            "minimum_order": 1,
            "image_url": "https://images.unsplash.com/photo-1518837695005-2083093ee35b?auto=format&fit=crop&w=1200&q=80",
        },
        {
            "name": "Java Fern",
            "category": "Epiphyte Plants",
            "description": "Low-maintenance fern that attaches to driftwood or rock and tolerates a wide range of water conditions.",
            "price": "349.00",
            "stock": 36,
            "minimum_order": 1,
            "image_url": "https://images.unsplash.com/photo-1501004318641-b39e6451bec6?auto=format&fit=crop&w=1200&q=80",
        },
        {
            "name": "Anubias Nana",
            "category": "Epiphyte Plants",
            "description": "Compact, slow-growing Anubias variety ideal for midground accents and shaded aquascapes.",
            "price": "299.00",
            "stock": 40,
            "minimum_order": 1,
            "image_url": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
        },
        {
            "name": "Water Wisteria",
            "category": "Midground Plants",
            "description": "Fast-growing stem plant with delicate lace-like leaves; excellent for nutrient uptake and fry cover.",
            "price": "259.00",
            "stock": 58,
            "minimum_order": 2,
            "image_url": "https://images.unsplash.com/photo-1527664557558-a2b352fcf203?auto=format&fit=crop&w=1200&q=80",
        },
        {
            "name": "Dwarf Hairgrass",
            "category": "Foreground Carpets",
            "description": "Fine-bladed carpeting species that forms lush, grassy meadows under strong light and CO2.",
            "price": "219.00",
            "stock": 60,
            "minimum_order": 2,
            "image_url": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?auto=format&fit=crop&w=1200&q=80",
        },
        {
            "name": "Hornwort",
            "category": "Floating Plants",
            "description": "Hardy, fast-growing oxygenator that can be floated or weighted; ideal for nutrient control.",
            "price": "199.00",
            "stock": 75,
            "minimum_order": 3,
            "image_url": "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=1200&q=80",
        },
        {
            "name": "Ludwigia Repens",
            "category": "Midground Plants",
            "description": "Copper-red stem plant that brings warm tones to aquascapes when provided with bright light.",
            "price": "279.00",
            "stock": 42,
            "minimum_order": 2,
            "image_url": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80",
        },
        {
            "name": "Bacopa Monnieri",
            "category": "Background Plants",
            "description": "Versatile medicinal herb with rounded leaves; tolerates trimming and submersed growth.",
            "price": "249.00",
            "stock": 54,
            "minimum_order": 2,
            "image_url": "https://images.unsplash.com/photo-1502082553048-f009c37129b9?auto=format&fit=crop&w=1200&q=80",
        },
        {
            "name": "Vallisneria Spiralis",
            "category": "Background Plants",
            "description": "Ribbon-like leaves create flowing under-water meadows; perfect for tall background coverage.",
            "price": "269.00",
            "stock": 48,
            "minimum_order": 2,
            "image_url": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=1200&q=80",
        },
        {
            "name": "Cabomba Caroliniana",
            "category": "Background Plants",
            "description": "Feathery aquatic stem plant loved for its fine texture and rapid growth in nutrient-rich tanks.",
            "price": "289.00",
            "stock": 46,
            "minimum_order": 2,
            "image_url": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80",
        },
    ]

    CATEGORY_DESCRIPTIONS = {
        "Background Plants": "Tall species suited for the rear of aquascapes to create depth and coverage.",
        "Epiphyte Plants": "Rhizome plants that attach to wood or rock instead of rooting in substrate.",
        "Midground Plants": "Mid-height plants that bridge the foreground carpet and taller background species.",
        "Foreground Carpets": "Low-growing carpeting plants for the front of the aquarium.",
        "Floating Plants": "Free-floating species that provide shade, cover, and nutrient absorption.",
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-download images even when a plant already exists.",
        )

    def handle(self, *args, **options):
        force = options.get("force", False)
        created_count = 0
        skipped = []

        with transaction.atomic():
            for plant_info in self.PLANT_DATA:
                plant = self._create_or_update_plant(plant_info, force_images=force)
                if plant is None:
                    skipped.append(plant_info["name"])
                else:
                    created_count += 1

        if created_count:
            self.stdout.write(self.style.SUCCESS(f"Seeded {created_count} plant(s) with images."))
        if skipped:
            names = ", ".join(skipped)
            self.stdout.write(self.style.WARNING(f"Skipped existing plants: {names}"))

    def _create_or_update_plant(self, data, force_images=False):
        category = self._get_or_create_category(data["category"])

        plant, created = Plant.objects.get_or_create(
            name=data["name"],
            defaults={
                "category": category,
                "description": data["description"],
                "price": Decimal(data["price"]),
                "stock_quantity": data["stock"],
                "minimum_order_quantity": data["minimum_order"],
                "is_active": True,
            },
        )

        if not created:
            if not force_images:
                return None
            # Update metadata when forcing refresh
            plant.category = category
            plant.description = data["description"]
            plant.price = Decimal(data["price"])
            plant.stock_quantity = data["stock"]
            plant.minimum_order_quantity = data["minimum_order"]

        image_downloaded = self._attach_image(plant, data["image_url"], force=force_images)

        plant.save()
        if not created and not image_downloaded and not force_images:
            return None
        return plant

    def _get_or_create_category(self, name):
        description = self.CATEGORY_DESCRIPTIONS.get(name, "")
        category, _ = Category.objects.get_or_create(
            name=name,
            defaults={
                "category_type": "plant",
                "description": description,
            },
        )
        if category.category_type != "plant":
            category.category_type = "plant"
        if description and category.description != description:
            category.description = description
        category.save()
        return category

    def _attach_image(self, plant, url, force=False):
        if plant.image and not force:
            return False

        try:
            response = requests.get(url, timeout=30, headers=self.HEADERS)
            response.raise_for_status()
        except requests.RequestException as exc:
            self.stderr.write(f"Failed to download image for {plant.name}: {exc}")
            return False

        file_ext = Path(urlparse(url).path).suffix or ".jpg"
        filename = f"{slugify(plant.name)}{file_ext}"
        plant.image.save(filename, ContentFile(response.content), save=False)
        return True
