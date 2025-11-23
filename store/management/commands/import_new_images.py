from django.core.management.base import BaseCommand
from django.conf import settings
import os
import shutil
from django.core.files import File


class Command(BaseCommand):
    help = 'Import images from assets/new_images into static/images or attach to Accessory objects.'

    def add_arguments(self, parser):
        parser.add_argument('--replace-static', action='store_true', help='Copy files into static/images (overwrite).')
        parser.add_argument('--attach-accessories', action='store_true', help='Attach images to Accessory objects by matching filename to accessory name.')
        parser.add_argument('--source', type=str, default=None, help='Source directory (defaults to <BASE_DIR>/assets/new_images).')

    def handle(self, *args, **options):
        base = getattr(settings, 'BASE_DIR', os.getcwd())
        source = options['source'] or os.path.join(base, 'assets', 'new_images')

        if not os.path.isdir(source):
            self.stdout.write(self.style.ERROR(f'Source directory not found: {source}'))
            self.stdout.write('Create the directory and place your image files there, then re-run this command.')
            return

        files = [f for f in os.listdir(source) if os.path.isfile(os.path.join(source, f))]
        if not files:
            self.stdout.write(self.style.WARNING(f'No files found in {source}'))
            return

        if options['replace_static']:
            dest_dir = os.path.join(base, 'static', 'images')
            if not os.path.isdir(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)
            for fname in files:
                src = os.path.join(source, fname)
                dst = os.path.join(dest_dir, fname)
                try:
                    shutil.copy2(src, dst)
                    self.stdout.write(self.style.SUCCESS(f'Copied {fname} -> static/images/'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Failed to copy {fname}: {e}'))

        if options['attach_accessories']:
            try:
                from store.models import Accessory
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to import Accessory model: {e}'))
                return

            from django.utils.text import slugify

            for fname in files:
                name, ext = os.path.splitext(fname)
                src = os.path.join(source, fname)
                # Try matching by exact name (case-insensitive) or slug
                acc = Accessory.objects.filter(name__iexact=name).first()
                if not acc:
                    acc = Accessory.objects.filter(slug__iexact=slugify(name)).first()

                if acc:
                    try:
                        with open(src, 'rb') as f:
                            django_file = File(f)
                            # Use save() so storage backend handles path
                            acc.image.save(fname, django_file, save=True)
                        self.stdout.write(self.style.SUCCESS(f'Attached {fname} to Accessory "{acc.name}" (id={acc.id})'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error attaching {fname} to Accessory {acc.id}: {e}'))
                else:
                    self.stdout.write(self.style.WARNING(f'No Accessory match for "{name}"; skipped attaching {fname}'))

        if not options['replace_static'] and not options['attach_accessories']:
            self.stdout.write('No action requested. Use --replace-static and/or --attach-accessories.')
