from django.core.management.base import BaseCommand
from store.models import Fish
import random
from decimal import Decimal


class Command(BaseCommand):
    help = 'Update all fish sizes with random values less than 5 inches'

    def handle(self, *args, **kwargs):
        fishes = Fish.objects.all()
        count = 0
        
        for fish in fishes:
            # Generate random size between 0.5 and 4.99 inches
            random_size = round(random.uniform(0.5, 4.99), 2)
            fish.size = Decimal(str(random_size))
            fish.save()
            count += 1
            self.stdout.write(f"Updated {fish.name}: {random_size} inches")
        
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully updated {count} fish sizes!'))
