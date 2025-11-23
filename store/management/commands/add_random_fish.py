from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import random
from decimal import Decimal

from store.models import Category, Breed, Fish


DEFAULT_CATEGORIES = {
    'Goldfish': ['Comet', 'Fantail'],
    'Betta': ['Veiltail', 'Crowntail'],
    'Guppy': ['Endler', 'Fancy'],
    'Cichlid': ['African', 'South American'],
    'Tetra': ['Neon', 'Cardinal']
}


def ensure_categories_and_breeds():
    if not Category.objects.exists():
        for cat_name, breeds in DEFAULT_CATEGORIES.items():
            cat = Category.objects.create(name=cat_name, description=f"{cat_name} category")
            for b in breeds:
                Breed.objects.create(name=b, category=cat, description=f"{b} breed")


def get_or_create_breed_for_category(category):
    breed = category.breeds.first()
    if not breed:
        breed = Breed.objects.create(name=f"{category.name}Breed", category=category)
    return breed


def random_price():
    return Decimal(str(round(random.uniform(50.0, 2000.0), 2)))


class Command(BaseCommand):
    help = 'Create random Fish records for testing'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=50, help='Number of fish to create')

    @transaction.atomic
    def handle(self, *args, **options):
        count = options.get('count', 50)
        ensure_categories_and_breeds()
        categories = list(Category.objects.all())
        created = 0

        for i in range(count):
            cat = random.choice(categories)
            breed = get_or_create_breed_for_category(cat)

            name = f"{breed.name} {random.randint(1000,9999)}"
            description = f"Test fish {name} in category {cat.name} and breed {breed.name}."
            price = random_price()
            size = round(random.uniform(0.5, 12.0), 2)
            stock_quantity = random.randint(0, 100)
            minimum_order_quantity = random.randint(1, 5)

            fish = Fish.objects.create(
                name=name,
                category=cat,
                breed=breed,
                description=description,
                price=price,
                size=size,
                stock_quantity=stock_quantity,
                minimum_order_quantity=minimum_order_quantity,
                is_available=(stock_quantity > 0),
                is_featured=(random.random() < 0.1),
            )
            created += 1
            self.stdout.write(self.style.SUCCESS(f"Created Fish: {fish.id} - {fish.name} (price={fish.price})"))

        self.stdout.write(self.style.SUCCESS(f"Finished: created {created} fish records."))
