from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
import requests
from django.core.files.base import ContentFile
from urllib.parse import quote_plus

from store.models import BlogPost, CustomUser


def download_placeholder(seed: int) -> bytes:
    url = f"https://picsum.photos/1200/600?random={seed}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.content
    except Exception:
        return None
    return None


class Command(BaseCommand):
    help = 'Create blog posts with placeholder images'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=1, help='Number of blog posts to create')

    @transaction.atomic
    def handle(self, *args, **options):
        count = options.get('count', 1)
        author = CustomUser.objects.filter(is_superuser=True).first() or CustomUser.objects.first()
        if not author:
            author = CustomUser.objects.create_user(username='blogadmin', email='blogadmin@example.com', password='password')
            self.stdout.write(self.style.WARNING('No users found; created demo author `blogadmin`.'))

        created = 0
        for i in range(count):
            title = f"Sample Blog Post {timezone.now().strftime('%Y%m%d%H%M%S')}_{i+1}"
            slug = quote_plus(title.lower().replace(' ', '-'))
            content = (
                "<p>This is a sample blog post generated for testing purposes. "
                "Replace with real content in admin panel.</p>"
            )
            excerpt = "Sample blog post for FISHY FRIEND AQUA."
            bp = BlogPost(title=title, slug=slug, author=author, excerpt=excerpt, content=content, is_published=True, published_at=timezone.now())
            bp.save()

            # assign placeholder image
            img_data = download_placeholder(4000 + i)
            if img_data:
                filename = f"blog_{bp.id}.jpg"
                try:
                    bp.image.save(filename, ContentFile(img_data), save=True)
                    self.stdout.write(self.style.SUCCESS(f"Created BlogPost {bp.id} with image: {bp.title}"))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Created BlogPost {bp.id} but failed to save image: {e}"))
            else:
                self.stdout.write(self.style.WARNING(f"Created BlogPost {bp.id} but failed to download placeholder image."))

            created += 1

        self.stdout.write(self.style.SUCCESS(f"Finished: created {created} blog posts."))
