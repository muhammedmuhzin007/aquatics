from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
import random

from store.models import LimitedOffer, Fish, Order, Review


SAMPLE_COMMENTS = [
    "Great quality, arrived healthy.",
    "Good packaging and fast delivery.",
    "Not as described, but customer service helped.",
    "Beautiful specimen, very happy with purchase.",
    "Satisfactory — would buy again.",
]


class Command(BaseCommand):
    help = "Seed the database with 5 LimitedOffer entries and 5 Review entries."

    def handle(self, *args, **options):
        offers_created = 0
        reviews_created = 0

        with transaction.atomic():
            fishes = list(Fish.objects.all())
            orders = list(Order.objects.all())

            # Create 5 limited offers
            for i in range(5):
                title = f"Limited Offer {i + 1}"
                discount = random.randint(10, 50)
                discount_text = f"Save {discount}%"

                start_time = timezone.now() - timedelta(days=random.randint(0, 2))
                end_time = start_time + timedelta(days=random.randint(3, 30))

                fish = random.choice(fishes) if fishes else None

                offer = LimitedOffer.objects.create(
                    title=title,
                    description=f"Special limited-time offer: {discount_text}",
                    discount_text=discount_text,
                    bg_color=f"#{random.randint(0, 0xFFFFFF):06x}",
                    fish=fish,
                    start_time=start_time,
                    end_time=end_time,
                    is_active=True,
                    show_on_homepage=True,
                )

                offers_created += 1

            # Create 5 reviews attached to random existing orders (if available)
            if not orders:
                self.stdout.write(self.style.ERROR("No orders found. Create orders first before seeding reviews."))
            else:
                selected_orders = random.sample(orders, min(5, len(orders)))
                for ord_obj in selected_orders:
                    user = ord_obj.user
                    rating = random.randint(1, 5)
                    comment = random.choice(SAMPLE_COMMENTS)
                    approved = random.choice([True, False])

                    # Avoid duplicate (user, order) by checking existence
                    if Review.objects.filter(user=user, order=ord_obj).exists():
                        continue

                    Review.objects.create(
                        user=user,
                        order=ord_obj,
                        rating=rating,
                        comment=comment,
                        approved=approved,
                    )
                    reviews_created += 1

        self.stdout.write(self.style.SUCCESS(f"Created {offers_created} limited offers and {reviews_created} reviews."))
