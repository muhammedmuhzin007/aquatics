from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File as DjangoFile
import os
import random


class Command(BaseCommand):
    help = 'Clear Accessory images and optionally assign images from Fish objects (by category or random fallback).'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Remove existing accessory images (files will be deleted from storage).')
        parser.add_argument('--assign', action='store_true', help='Assign fish images to accessories.')
        parser.add_argument('--commit', action='store_true', help='Perform changes. Without --commit runs as dry-run and only prints actions.')
        parser.add_argument('--remove-files', action='store_true', help='When clearing, remove files from storage. Default behavior is to unset field only.')

    def handle(self, *args, **options):
        clear = options['clear']
        assign = options['assign']
        commit = options['commit']
        remove_files = options['remove_files']

        if not clear and not assign:
            self.stdout.write(self.style.ERROR('No action specified. Use --clear and/or --assign.'))
            return

        try:
            from store.models import Accessory, Fish, FishMedia
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to import models: {e}'))
            return

        accessories = Accessory.objects.all()
        if not accessories.exists():
            self.stdout.write(self.style.WARNING('No accessories found.'))
            return

        # Prebuild fish lookup per category
        fish_by_category = {}
        all_fish_with_images = []
        for fish in Fish.objects.all():
            # find an image: prefer fish.image, then first FishMedia.file
            image_field = None
            if fish.image:
                image_field = fish.image
            else:
                fm = fish.media.filter(media_type='image', file__isnull=False).first()
                if fm and fm.file:
                    image_field = fm.file

            if image_field:
                all_fish_with_images.append((fish, image_field))
                cat_id = fish.category_id
                fish_by_category.setdefault(cat_id, []).append((fish, image_field))

        if not all_fish_with_images:
            self.stdout.write(self.style.WARNING('No fish images available to assign.'))
            if clear and not commit:
                self.stdout.write(self.style.SUCCESS('Dry-run: would clear accessory images.'))
            return

        actions = []

        for acc in accessories:
            if clear and acc.image:
                actions.append({'action': 'clear', 'accessory': acc, 'old_name': acc.image.name})

            if assign:
                chosen = None
                # Try to pick fish in same category
                if acc.category_id and acc.category_id in fish_by_category:
                    chosen = random.choice(fish_by_category[acc.category_id])
                else:
                    # fallback to any fish with image
                    chosen = random.choice(all_fish_with_images) if all_fish_with_images else None

                if chosen:
                    fish_obj, image_field = chosen
                    # determine source name and extension
                    src_name = getattr(image_field, 'name', None)
                    if src_name:
                        _, ext = os.path.splitext(src_name)
                        dest_name = f"{acc.id}-{acc.name.replace(' ', '_')}{ext}"
                    else:
                        dest_name = None

                    actions.append({'action': 'assign', 'accessory': acc, 'fish': fish_obj, 'source': image_field, 'dest_name': dest_name})

        # Report planned actions
        self.stdout.write('Planned actions:')
        for act in actions:
            if act['action'] == 'clear':
                self.stdout.write(f"  CLEAR image for Accessory id={act['accessory'].id} name='{act['accessory'].name}' (file={act['old_name']})")
            else:
                self.stdout.write(f"  ASSIGN image for Accessory id={act['accessory'].id} name='{act['accessory'].name}' from Fish id={act['fish'].id} name='{act['fish'].name}' source='{getattr(act['source'], 'name', None)}'")

        if not commit:
            self.stdout.write(self.style.SUCCESS('Dry-run complete. No changes made. Re-run with --commit to apply.'))
            return

        # Execute actions
        for act in actions:
            acc = act['accessory']
            if act['action'] == 'clear':
                try:
                    if remove_files and acc.image:
                        try:
                            acc.image.delete(save=False)
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f'Failed to delete file for Accessory {acc.id}: {e}'))
                    acc.image = None
                    acc.save()
                    self.stdout.write(self.style.SUCCESS(f'Cleared image for Accessory id={acc.id}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error clearing image for Accessory id={acc.id}: {e}'))

            elif act['action'] == 'assign':
                src_field = act['source']
                try:
                    # Open source file and save to accessory.image
                    # Some fields may be FileField instances (fish.image or FishMedia.file)
                    src_field.open()
                    with src_field.open('rb') as f:
                        django_file = DjangoFile(f)
                        new_name = act['dest_name'] or os.path.basename(getattr(src_field, 'name', 'image'))
                        acc.image.save(new_name, django_file, save=True)
                    self.stdout.write(self.style.SUCCESS(f'Assigned image to Accessory id={acc.id} from Fish id={act["fish"].id}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Failed to assign image to Accessory id={acc.id}: {e}'))

        self.stdout.write(self.style.SUCCESS('Completed applying changes.'))
