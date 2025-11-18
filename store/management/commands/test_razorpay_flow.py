from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Removed. Use Stripe or mock provider tests instead.'

    def handle(self, *args, **options):
        raise CommandError('This management command was removed. Use store.management commands for Stripe or mock provider tests.')
