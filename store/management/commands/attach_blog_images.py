import os
from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from store.models import BlogPost

class Command(BaseCommand):
    help = 'Attach sample images from static/images to sample blog posts'

    def handle(self, *args, **options):
        images = ['hero-betta-fish.png', 'image.png', 'image1.png', 'underwater.jpg']
        static_images_dir = os.path.join(settings.BASE_DIR, 'static', 'images')
        attached = []

        for i in range(1, 6):
            slug = f'sample-blog-post-{i}'
            try:
                post = BlogPost.objects.get(slug=slug)
            except BlogPost.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Post with slug {slug} not found, skipping'))
                continue

            img_name = images[(i-1) % len(images)]
            src_path = os.path.join(static_images_dir, img_name)
            if not os.path.exists(src_path):
                self.stdout.write(self.style.ERROR(f'Image not found: {src_path}'))
                continue

            dest_filename = f'blog/{slug}-{img_name}'
            with open(src_path, 'rb') as f:
                django_file = File(f)
                post.image.save(dest_filename, django_file, save=True)
                attached.append((post.id, post.slug, dest_filename))
                self.stdout.write(self.style.SUCCESS(f'Attached {dest_filename} to {post.slug}'))

        self.stdout.write('Done. Attached images: ' + str(attached))
