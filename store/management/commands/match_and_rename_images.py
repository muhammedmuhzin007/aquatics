from django.core.management.base import BaseCommand
from django.conf import settings
import os
from django.utils.text import slugify
from difflib import get_close_matches


class Command(BaseCommand):
    help = 'Match images in a source folder to Accessory names and rename them to accessory slugs. Use --commit to perform renames and --attach to save to Accessory.image.'

    def add_arguments(self, parser):
        parser.add_argument('--source', type=str, default=None, help='Source directory (defaults to <BASE_DIR>/assets/new_images).')
        parser.add_argument('--dry-run', action='store_true', help='Only show proposed renames (default).')
        parser.add_argument('--commit', action='store_true', help='Perform actual file renames.')
        parser.add_argument('--attach', action='store_true', help='After renaming, attach image to Accessory.image (requires --commit).')
        parser.add_argument('--min-score', type=float, default=0.6, help='Minimum fuzzy match cutoff (0-1).')

    def handle(self, *args, **options):
        base = getattr(settings, 'BASE_DIR', os.getcwd())
        source = options['source'] or os.path.join(base, 'assets', 'new_images')
        dry_run = options['dry_run']
        commit = options['commit']
        attach = options['attach']
        min_score = options['min_score']

        if attach and not commit:
            self.stdout.write(self.style.ERROR('The --attach option requires --commit to actually rename files first.'))
            return

        if not os.path.isdir(source):
            self.stdout.write(self.style.ERROR(f'Source directory not found: {source}'))
            return

        files = [f for f in os.listdir(source) if os.path.isfile(os.path.join(source, f))]
        if not files:
            self.stdout.write(self.style.WARNING(f'No files found in {source}'))
            return

        # Build lookup of file basenames without extension
        file_map = {}
        for f in files:
            name, ext = os.path.splitext(f)
            file_map[name.lower()] = (f, ext)

        try:
            from store.models import Accessory
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to import Accessory model: {e}'))
            return

        accessories = Accessory.objects.filter(is_active=True)
        if not accessories.exists():
            self.stdout.write(self.style.WARNING('No active accessories found in database.'))
            return

        proposed = []

        # For each accessory, try exact match by name or slug, then fuzzy match
        file_keys = list(file_map.keys())
        for acc in accessories:
            acc_name = (acc.name or '').strip()
            acc_slug = slugify(acc_name)
            candidates = []

            # exact by name
            if acc_name and acc_name.lower() in file_map:
                candidates.append(file_map[acc_name.lower()][0])

            # exact by slug
            if acc_slug and acc_slug.lower() in file_map and file_map[acc_slug.lower()][0] not in candidates:
                candidates.append(file_map[acc_slug.lower()][0])

            # fuzzy match on basename
            if not candidates and file_keys:
                # get_close_matches returns list of keys (lowercased basenames)
                matches = get_close_matches(acc_name.lower() or acc_slug.lower(), file_keys, n=1, cutoff=min_score)
                if matches:
                    matched_key = matches[0]
                    candidates.append(file_map[matched_key][0])

            if candidates:
                src_fname = candidates[0]
                _, ext = os.path.splitext(src_fname)
                dest_fname = f"{acc_slug}{ext}"
                src_path = os.path.join(source, src_fname)
                dest_path = os.path.join(source, dest_fname)
                proposed.append((acc, src_fname, dest_fname, src_path, dest_path))

        if not proposed:
            self.stdout.write(self.style.WARNING('No candidate matches found between accessories and images.'))
            return

        # Show proposed changes
        self.stdout.write('Proposed renames:')
        for acc, src, dest, _, _ in proposed:
            self.stdout.write(f'  {src} -> {dest}  (Accessory: "{acc.name}" id={acc.id})')

        if dry_run and not commit:
            self.stdout.write(self.style.SUCCESS('Dry run complete. No files were changed.'))
            return

        # Perform renames
        for acc, src, dest, src_path, dest_path in proposed:
            try:
                # Avoid overwriting existing destination file — create a numbered suffix if needed
                final_dest = dest_path
                if os.path.exists(final_dest):
                    base_name, ext = os.path.splitext(dest)
                    i = 1
                    while True:
                        candidate = os.path.join(source, f"{base_name}-{i}{ext}")
                        if not os.path.exists(candidate):
                            final_dest = candidate
                            break
                        i += 1

                os.rename(src_path, final_dest)
                new_fname = os.path.basename(final_dest)
                self.stdout.write(self.style.SUCCESS(f'Renamed {src} -> {new_fname}'))

                # Optionally attach to accessory.image
                if attach:
                    try:
                        from django.core.files import File as DjangoFile
                        with open(final_dest, 'rb') as f:
                            django_file = DjangoFile(f)
                            acc.image.save(new_fname, django_file, save=True)
                        self.stdout.write(self.style.SUCCESS(f'Attached {new_fname} to Accessory "{acc.name}" (id={acc.id})'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Failed to attach {new_fname} to Accessory {acc.id}: {e}'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to rename {src} -> {dest}: {e}'))

        self.stdout.write(self.style.SUCCESS('Operation complete.'))
