from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
import random

from store.models import LimitedOffer, Fish


def random_hex_color():
    return "#%06x" % random.randint(0, 0xFFFFFF)


class Command(BaseCommand):
    help = 'Create random LimitedOffer records for testing'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=10, help='Number of offers to create')

    @transaction.atomic
    def handle(self, *args, **options):
        count = options.get('count', 10)
        fishes = list(Fish.objects.all())
        if not fishes:
            self.stdout.write(self.style.ERROR('No Fish found in database. Create fishes first.'))
            return

        created = 0
        now = timezone.now()
        for i in range(count):
            fish = random.choice(fishes)
            start = now
            # random duration between 7 and 30 days
            end = now + timezone.timedelta(days=random.randint(7, 30))
            title = f"Limited Offer {random.randint(1000,9999)}"
            discount = random.choice(["Save 10%","Save 20%","Flat ₹100 Off","Flat ₹250 Off","Save 25%"])
            offer = LimitedOffer.objects.create(
                title=title,
                description=f"Special limited time offer on {fish.name}",
                discount_text=discount,
                bg_color=random_hex_color(),
                fish=fish,
                start_time=start,
                end_time=end,
                is_active=True,
                show_on_homepage=random.choice([True, False]),
            )
            created += 1
            self.stdout.write(self.style.SUCCESS(f"Created Offer: {offer.id} - {offer.title} for Fish {fish.id}"))

        self.stdout.write(self.style.SUCCESS(f"Finished: created {created} offers."))
