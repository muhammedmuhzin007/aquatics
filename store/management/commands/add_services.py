from django.core.management.base import BaseCommand
from django.db import transaction
import random

from store.models import Service

SAMPLE_SERVICES = [
    "Aquarium Setup",
    "Water Testing & Conditioning",
    "Tank Cleaning",
    "Fish Health Check",
    "Custom Aquarium Design",
    "Livestock Sourcing",
    "Filter Maintenance",
    "Heater Installation",
    "Aquascaping",
    "Monthly Maintenance Plan",
    "Planting & Hardscape",
    "Lighting Optimization",
]


class Command(BaseCommand):
    help = 'Create random Service records for testing'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=10, help='Number of services to create')

    @transaction.atomic
    def handle(self, *args, **options):
        count = options.get('count', 10)
        created = 0
        for i in range(count):
            title = SAMPLE_SERVICES[i % len(SAMPLE_SERVICES)]
            # Ensure titles are unique by appending a suffix when duplicates would occur
            suffix = '' if i < len(SAMPLE_SERVICES) else f' {i+1}'
            desc = (
                f"{title} — Professional service to help with {title.lower()}. "
                "Our experts ensure healthy, vibrant aquariums and happy fish."
            )

            svc = Service.objects.create(
                title=title + suffix,
                description=desc,
                is_active=True,
                display_order=i,
            )
            created += 1
            self.stdout.write(self.style.SUCCESS(f"Created Service: {svc.id} - {svc.title}"))

        self.stdout.write(self.style.SUCCESS(f"Finished: created {created} service records."))
