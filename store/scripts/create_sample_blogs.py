from django.utils import timezone
from datetime import timedelta
from store.models import BlogPost, CustomUser

now = timezone.now()
# Prefer an admin user if available
author = CustomUser.objects.filter(role='admin').first() or CustomUser.objects.filter(is_superuser=True).first()
if author:
    print('Using author:', author.username)
else:
    print('No admin author found; posts will have no author (author=None)')

created = []
for i in range(1, 6):
    title = f"Sample Blog Post {i}"
    base_slug = f"sample-blog-post-{i}"
    slug = base_slug
    j = 1
    while BlogPost.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{j}"
        j += 1
    excerpt = f"This is a sample excerpt for blog post {i}."
    content = ("This is sample blog post content for post " + str(i) + ".\n\n") * 3 + "More details about aquarium care."
    published_at = now - timedelta(days=(5 - i))

    post = BlogPost(title=title, slug=slug, author=author, excerpt=excerpt, content=content, is_published=True, published_at=published_at)
    post.save()
    created.append((post.id, post.slug, str(post.published_at)))
    print('Created', post.id, post.slug, post.published_at)

print('Done. Created posts:', created)
