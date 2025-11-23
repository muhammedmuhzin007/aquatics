from django.core.management.base import BaseCommand
from django.db import transaction
import random

from store.models import Review, CustomUser

SAMPLE_COMMENTS = [
    "Excellent quality and fast delivery.",
    "Fish arrived healthy and vibrant. Highly recommend!",
    "Good seller, packaging could be better.",
    "Very satisfied with the purchase.",
    "Not as described, but customer support helped.",
    "Lovely fish, will buy again.",
    "Great selection and responsive seller.",
    "The fish was smaller than pictured but healthy.",
    "Fantastic colours and active fish.",
    "Decent price and quick shipping."
]


class Command(BaseCommand):
    help = 'Create random Review records for testing'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=10, help='Number of reviews to create')

    @transaction.atomic
    def handle(self, *args, **options):
        count = options.get('count', 10)
        users = list(CustomUser.objects.filter(is_active=True))

        # If no users exist, create a demo user
        if not users:
            demo = CustomUser.objects.create_user(username='testuser', email='testuser@example.com', password='testpass')
            users = [demo]
            self.stdout.write(self.style.WARNING('No users found; created demo user `testuser`.'))

        created = 0
        for i in range(count):
            user = random.choice(users)
            rating = random.randint(1, 5)
            comment = random.choice(SAMPLE_COMMENTS)
            approved = random.choice([True, False])

            review = Review.objects.create(
                user=user,
                order=None,
                rating=rating,
                comment=comment,
                approved=approved,
            )
            created += 1
            self.stdout.write(self.style.SUCCESS(f'Created Review: {review.id} by {user.username} ({rating}★)'))

        self.stdout.write(self.style.SUCCESS(f'Finished: created {created} review records.'))
