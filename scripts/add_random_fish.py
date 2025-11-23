import random
from decimal import Decimal

from store.models import Category, Breed, Fish


def ensure_categories_and_breeds():
    # If there are no categories, create some default fish categories and breeds
    if not Category.objects.exists():
        default_categories = {
            'Goldfish': ['Comet', 'Fantail'],
            'Betta': ['Veiltail', 'Crowntail'],
            'Guppy': ['Endler', 'Fancy'],
            'Cichlid': ['African', 'South American'],
            'Tetra': ['Neon', 'Cardinal']
        }
        for cat_name, breeds in default_categories.items():
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


def create_random_fish(count=50):
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
        print(f"Created Fish: {fish.name} (id={fish.id}) price={fish.price}")

    print(f"Finished: created {created} fish records.")


if __name__ == '__main__':
    create_random_fish(50)
