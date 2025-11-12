from django.core.management.base import BaseCommand
import random

from store.models import Fish


class Command(BaseCommand):
    help = "Mark N random fishes as featured (default 8)."

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=8, help='Number of fishes to mark as featured')

    def handle(self, *args, **options):
        count = options.get('count', 8)
        fishes = list(Fish.objects.all())
        if not fishes:
            self.stdout.write(self.style.ERROR('No fishes found to mark as featured.'))
            return

        selected = random.sample(fishes, min(count, len(fishes)))
        for f in selected:
            f.is_featured = True
            f.save(update_fields=['is_featured'])

        self.stdout.write(self.style.SUCCESS(f'Marked {len(selected)} fishes as featured.'))
