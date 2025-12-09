import os
import random
import requests
from io import BytesIO
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.text import slugify
from store.models import BlogPost, CustomUser


PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"

BLOG_POSTS = [
    {
        'title': 'Complete Guide to Fish Tank Setup',
        'excerpt': 'Learn how to set up your first aquarium correctly with our step-by-step guide.',
        'content': '''
        <h3>Setting Up Your First Aquarium</h3>
        <p>Setting up an aquarium properly is crucial for the health and happiness of your fish. This comprehensive guide covers everything you need to know.</p>
        <h4>Essential Equipment</h4>
        <ul>
            <li>Tank (minimum 20 gallons for beginners)</li>
            <li>Filter system</li>
            <li>Heater (for tropical fish)</li>
            <li>Lighting</li>
            <li>Substrate</li>
            <li>Decorations and plants</li>
        </ul>
        <p>Follow these steps carefully to ensure your fish thrive in their new home.</p>
        ''',
        'query': 'aquarium setup tank',
    },
    {
        'title': 'Best Beginner Fish Species',
        'excerpt': 'Discover which fish species are perfect for aquarium beginners.',
        'content': '''
        <h3>Beginner-Friendly Fish</h3>
        <p>Not all fish are suitable for beginners. Here are the best species to start with:</p>
        <h4>Top 5 Beginner Fish</h4>
        <ol>
            <li><strong>Goldfish</strong> - Hardy and colorful</li>
            <li><strong>Guppies</strong> - Small and peaceful</li>
            <li><strong>Tetras</strong> - Beautiful schooling fish</li>
            <li><strong>Bettas</strong> - Stunning and low-maintenance</li>
            <li><strong>Corydoras Catfish</strong> - Great tank cleaners</li>
        </ol>
        <p>These species are forgiving and great for learning aquarium care.</p>
        ''',
        'query': 'beginner fish species',
    },
    {
        'title': 'Fish Feeding Guide and Schedules',
        'excerpt': 'Proper feeding is essential for your fish health. Here\'s everything you need to know.',
        'content': '''
        <h3>How to Feed Your Fish Properly</h3>
        <p>Overfeeding is one of the most common mistakes in fishkeeping. Learn the right way to feed your aquatic pets.</p>
        <h4>Feeding Guidelines</h4>
        <ul>
            <li>Feed small amounts 1-2 times daily</li>
            <li>Only feed what they can eat in 5 minutes</li>
            <li>Skip one day per week for fasting</li>
            <li>Vary food types for nutrition</li>
        </ul>
        <p>Different species have different dietary needs. Always research your specific fish.</p>
        ''',
        'query': 'fish feeding',
    },
    {
        'title': 'Water Chemistry Basics for Aquariums',
        'excerpt': 'Understanding pH, hardness, and ammonia is crucial for a healthy tank.',
        'content': '''
        <h3>Essential Water Parameters</h3>
        <p>Your fish live in the water, so its chemistry is everything. Here are the key parameters:</p>
        <h4>Important Measurements</h4>
        <ul>
            <li><strong>pH:</strong> 6.0-7.5 for most freshwater fish</li>
            <li><strong>Ammonia:</strong> Should be 0 ppm</li>
            <li><strong>Nitrite:</strong> Should be 0 ppm</li>
            <li><strong>Nitrate:</strong> Below 20 ppm</li>
            <li><strong>Temperature:</strong> 74-82°F depending on species</li>
        </ul>
        <p>Test your water regularly to maintain optimal conditions.</p>
        ''',
        'query': 'water chemistry ph ammonia',
    },
    {
        'title': 'Aquarium Maintenance Tips',
        'excerpt': 'Keep your tank clean and healthy with our maintenance checklist.',
        'content': '''
        <h3>Regular Maintenance Schedule</h3>
        <p>Consistent maintenance keeps your aquarium healthy and your fish happy.</p>
        <h4>Daily Tasks</h4>
        <ul>
            <li>Feed fish appropriate amounts</li>
            <li>Check temperature and equipment</li>
            <li>Observe fish behavior</li>
        </ul>
        <h4>Weekly Tasks</h4>
        <ul>
            <li>Test water parameters</li>
            <li>Perform partial water change (25%)</li>
            <li>Clean filter intake</li>
        </ul>
        <h4>Monthly Tasks</h4>
        <ul>
            <li>Deep clean decorations</li>
            <li>Inspect equipment</li>
            <li>Trim aquatic plants</li>
        </ul>
        ''',
        'query': 'aquarium maintenance cleaning',
    },
    {
        'title': 'Common Fish Diseases and Treatments',
        'excerpt': 'Identify and treat common aquarium fish diseases.',
        'content': '''
        <h3>Keeping Your Fish Healthy</h3>
        <p>Prevention is better than cure. Learn to identify common diseases early.</p>
        <h4>Common Diseases</h4>
        <ul>
            <li><strong>Ich (White Spot):</strong> White spots on body, raise temperature</li>
            <li><strong>Fin Rot:</strong> Frayed fins, improve water quality</li>
            <li><strong>Dropsy:</strong> Swollen body, isolate fish, treat with salt</li>
            <li><strong>Velvet:</strong> Gold dust appearance, use medication</li>
        </ul>
        <p>Always quarantine sick fish to prevent spread to the entire tank.</p>
        ''',
        'query': 'fish disease treatment',
    },
    {
        'title': 'Exotic Fish Species You Should Know',
        'excerpt': 'Explore stunning exotic species for advanced aquarists.',
        'content': '''
        <h3>Exotic Fish Worth Considering</h3>
        <p>Once you've mastered the basics, explore these beautiful exotic species.</p>
        <h4>Popular Exotic Fish</h4>
        <ul>
            <li><strong>Discus:</strong> Beautiful but demanding</li>
            <li><strong>Angelfish:</strong> Elegant and graceful</li>
            <li><strong>Rasbora:</strong> Colorful schooling fish</li>
            <li><strong>Killifish:</strong> Unique and vibrant</li>
        </ul>
        <p>These species require more experience and better water conditions.</p>
        ''',
        'query': 'exotic tropical fish',
    },
    {
        'title': 'Live Plants for Your Aquarium',
        'excerpt': 'Discover the benefits of adding live plants to your tank.',
        'content': '''
        <h3>Benefits of Aquatic Plants</h3>
        <p>Live plants aren't just decorative—they improve water quality and create natural habitats.</p>
        <h4>Easy Beginner Plants</h4>
        <ul>
            <li><strong>Java Fern:</strong> Low light, hardy</li>
            <li><strong>Anubias:</strong> Slow growing, decorative</li>
            <li><strong>Hornwort:</strong> Fast growing, oxygenates water</li>
            <li><strong>Marimo Moss Ball:</strong> Unique and easy</li>
        </ul>
        <p>Plants help reduce nitrates and provide oxygen for your fish.</p>
        ''',
        'query': 'aquatic plants moss',
    },
    {
        'title': 'Breeding Fish at Home',
        'excerpt': 'A guide to successfully breeding your aquarium fish.',
        'content': '''
        <h3>Getting Started with Fish Breeding</h3>
        <p>Breeding fish can be rewarding but requires dedication and knowledge.</p>
        <h4>Prerequisites for Breeding</h4>
        <ul>
            <li>Separate breeding tank</li>
            <li>Proper water conditions</li>
            <li>Healthy, mature fish</li>
            <li>Adequate food for fry</li>
            <li>Patience and observation</li>
        </ul>
        <p>Different species have different breeding requirements. Research thoroughly before attempting.</p>
        ''',
        'query': 'fish breeding',
    },
    {
        'title': 'Creating the Perfect Fish Tank Environment',
        'excerpt': 'Design a beautiful and healthy aquarium that your fish will love.',
        'content': '''
        <h3>Aquarium Design Tips</h3>
        <p>A well-designed tank is not only beautiful but also supports fish health.</p>
        <h4>Design Principles</h4>
        <ul>
            <li>Provide hiding spots with plants and decorations</li>
            <li>Create open swimming areas</li>
            <li>Use natural colors and materials</li>
            <li>Consider the natural habitat of your fish</li>
            <li>Ensure proper lighting for 8-10 hours daily</li>
        </ul>
        <p>Your fish will be healthier and happier in a well-designed environment.</p>
        ''',
        'query': 'aquarium design decoration',
    },
]


def fetch_pexels_image(query: str) -> bytes:
    """Fetch a real image from Pexels API."""
    if not PEXELS_API_KEY:
        return None
    
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": query, "per_page": 1}
    
    try:
        resp = requests.get(PEXELS_SEARCH_URL, headers=headers, params=params, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
        photos = data.get("photos") or []
        if not photos:
            return None
        photo_url = photos[0].get("src", {}).get("large") or photos[0].get("src", {}).get("medium")
        if not photo_url:
            return None
        img_resp = requests.get(photo_url, timeout=10)
        if img_resp.status_code == 200:
            return img_resp.content
    except Exception as e:
        print(f"Pexels fetch error: {e}")
    
    return None


def generate_placeholder_image(title: str) -> bytes:
    """Generate a fallback placeholder image."""
    colors = [
        (25, 118, 210),
        (56, 142, 60),
        (229, 57, 53),
        (251, 140, 0),
        (103, 58, 183),
        (0, 150, 136),
        (244, 67, 54),
        (33, 150, 243),
        (76, 175, 80),
        (255, 193, 7),
    ]
    color = colors[hash(title) % len(colors)]
    
    img = Image.new('RGB', (800, 400), color)
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype('arial.ttf', 40)
    except Exception:
        font = ImageFont.load_default()
    
    tw, th = draw.textbbox((0, 0), title, font=font)[2:]
    draw.text(((800 - tw) // 2, (400 - th) // 2), title, fill=(255, 255, 255), font=font)
    
    buf = BytesIO()
    img.save(buf, format='JPEG', quality=85)
    return buf.getvalue()


def add_blog_posts():
    """Create 10 blog posts with images."""
    # Get or create author
    author, _ = CustomUser.objects.get_or_create(
        username='blogger',
        defaults={'email': 'blogger@fishyfriendaqua.com', 'role': 'admin'}
    )
    
    created = 0
    for idx, post_data in enumerate(BLOG_POSTS):
        slug = slugify(post_data['title'])
        
        blog, is_new = BlogPost.objects.get_or_create(
            slug=slug,
            defaults={
                'title': post_data['title'],
                'author': author,
                'excerpt': post_data['excerpt'],
                'content': post_data['content'],
                'is_published': True,
                'published_at': timezone.now() - timedelta(days=10 - idx),
            }
        )
        
        if is_new and not blog.image:
            # Try Pexels first
            img_data = fetch_pexels_image(post_data['query'])
            
            # Fallback to placeholder
            if not img_data:
                img_data = generate_placeholder_image(post_data['title'])
            
            if img_data:
                filename = f"blog_{blog.id}_{slug}.jpg"
                blog.image.save(filename, ContentFile(img_data), save=True)
                created += 1
                print(f"Created Blog: {blog.title}")
        else:
            print(f"Blog already exists: {blog.title}")
    
    print(f"Total blog posts created: {created}")


if __name__ == '__main__':
    add_blog_posts()
