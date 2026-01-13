"""
Management command to optimize images
Usage: python manage.py optimize_images
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from PIL import Image
import os


class Command(BaseCommand):
    help = 'Optimizes all images in media directory'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-size',
            type=int,
            default=1200,
            help='Maximum width/height in pixels (default: 1200)',
        )
        parser.add_argument(
            '--quality',
            type=int,
            default=85,
            help='JPEG quality (default: 85)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        max_size = options['max_size']
        quality = options['quality']
        dry_run = options['dry_run']
        
        media_root = settings.MEDIA_ROOT
        if not os.path.exists(media_root):
            self.stdout.write(self.style.ERROR(f'Media root not found: {media_root}'))
            return
        
        optimized_count = 0
        skipped_count = 0
        error_count = 0
        
        # Walk through media directory
        for root, dirs, files in os.walk(media_root):
            for filename in files:
                if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    continue
                
                filepath = os.path.join(root, filename)
                
                try:
                    with Image.open(filepath) as img:
                        width, height = img.size
                        
                        # Check if image needs optimization
                        if width > max_size or height > max_size:
                            if dry_run:
                                self.stdout.write(f'Would optimize: {filepath} ({width}x{height})')
                            else:
                                # Calculate new size maintaining aspect ratio
                                if width > height:
                                    new_width = max_size
                                    new_height = int(height * (max_size / width))
                                else:
                                    new_height = max_size
                                    new_width = int(width * (max_size / height))
                                
                                # Resize image
                                img_resized = img.resize((new_width, new_height), Image.LANCZOS)
                                
                                # Save with optimization
                                if img.format == 'PNG':
                                    img_resized.save(filepath, 'PNG', optimize=True)
                                else:
                                    img_resized.save(filepath, 'JPEG', quality=quality, optimize=True)
                                
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f'Optimized: {filepath} ({width}x{height} → {new_width}x{new_height})'
                                    )
                                )
                            
                            optimized_count += 1
                        else:
                            skipped_count += 1
                
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'Error processing {filepath}: {str(e)}')
                    )
        
        # Summary
        self.stdout.write('\n' + '='*60)
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes made'))
        self.stdout.write(f'Images that would be optimized: {optimized_count}')
        self.stdout.write(f'Images already optimal: {skipped_count}')
        if error_count:
            self.stdout.write(self.style.ERROR(f'Errors: {error_count}'))
        self.stdout.write('='*60)
