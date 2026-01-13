"""
Management command to clear all cache
Usage: python manage.py clear_cache
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache


class Command(BaseCommand):
    help = 'Clears all cache'

    def add_arguments(self, parser):
        parser.add_argument(
            '--key',
            type=str,
            help='Clear specific cache key',
        )

    def handle(self, *args, **options):
        key = options.get('key')
        
        if key:
            cache.delete(key)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully cleared cache key: {key}')
            )
        else:
            cache.clear()
            self.stdout.write(
                self.style.SUCCESS('Successfully cleared all cache')
            )
