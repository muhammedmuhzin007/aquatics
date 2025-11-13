from django.core.management.base import BaseCommand
from django.db import transaction
from store.models import Service

SERVICES = [
    {
        'title': 'Tank Setup Consultation',
        'description': 'Personalized tank setup advice including filtration, substrate, and compatibility recommendations.',
        'display_order': 1,
    },
    {
        'title': 'Water Testing & Conditioning',
        'description': 'Comprehensive water testing and conditioning to ensure optimal water parameters for your fishes.',
        'display_order': 2,
    },
    {
        'title': 'Disease Diagnosis & Treatment',
        'description': 'Professional diagnosis and treatment plans for common aquarium diseases and quarantine guidance.',
        'display_order': 3,
    },
    {
        'title': 'Aquascaping Service',
        'description': 'Custom aquascaping service including plant selection, hardscape placement, and maintenance tips.',
        'display_order': 4,
    },
    {
        'title': 'Livestock Delivery & Acclimation',
        'description': 'Safe transportation, delivery and acclimation service for new fish arrivals to minimize stress.',
        'display_order': 5,
    },
]


class Command(BaseCommand):
    help = 'Seed the database with 5 default services (idempotent).'

    def handle(self, *args, **options):
        created = 0
        updated = 0
        with transaction.atomic():
            for s in SERVICES:
                obj, created_flag = Service.objects.get_or_create(
                    title=s['title'],
                    defaults={
                        'description': s['description'],
                        'display_order': s.get('display_order', 0),
                        'is_active': True,
                    }
                )
                if created_flag:
                    created += 1
                else:
                    # Ensure fields are up-to-date
                    changed = False
                    if obj.description != s['description']:
                        obj.description = s['description']
                        changed = True
                    if obj.display_order != s.get('display_order', 0):
                        obj.display_order = s.get('display_order', 0)
                        changed = True
                    if not obj.is_active:
                        obj.is_active = True
                        changed = True
                    if changed:
                        obj.save()
                        updated += 1

        self.stdout.write(self.style.SUCCESS(f'Services seeded: created={created}, updated={updated}'))
