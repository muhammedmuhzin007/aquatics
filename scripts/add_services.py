from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile
from store.models import Service


SERVICES = [
    {
        'title': 'Free Delivery',
        'description': 'We offer free delivery on all orders across Mumbai and nearby areas. Your aquatic friends will arrive safe and sound at your doorstep.',
        'order': 0,
    },
    {
        'title': 'Expert Consultation',
        'description': 'Our team of aquarium experts is available to provide guidance on fish care, tank setup, maintenance, and species compatibility.',
        'order': 1,
    },
    {
        'title': 'Quality Assurance',
        'description': 'Every fish is carefully inspected and quarantined before shipping. We guarantee healthy, vibrant fishes or your money back.',
        'order': 2,
    },
    {
        'title': '24/7 Customer Support',
        'description': 'Have questions? Our dedicated support team is available around the clock to assist you via phone, email, or WhatsApp.',
        'order': 3,
    },
]


def generate_placeholder_image(title: str) -> bytes:
    """Generate a colored placeholder image for the service."""
    colors = [
        (25, 118, 210),    # blue
        (56, 142, 60),     # green
        (229, 57, 53),     # red
        (251, 140, 0),     # orange
    ]
    color = colors[hash(title) % len(colors)]
    
    img = Image.new('RGB', (600, 400), color)
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype('arial.ttf', 40)
    except Exception:
        font = ImageFont.load_default()
    
    tw, th = draw.textbbox((0, 0), title, font=font)[2:]
    draw.text(((600 - tw) // 2, (400 - th) // 2), title, fill=(255, 255, 255), font=font)
    
    buf = BytesIO()
    img.save(buf, format='JPEG', quality=85)
    return buf.getvalue()


def add_services():
    """Create 4 sample services for FISHY FRIEND AQUA."""
    created = 0
    for service_data in SERVICES:
        service, is_new = Service.objects.get_or_create(
            title=service_data['title'],
            defaults={
                'description': service_data['description'],
                'display_order': service_data['order'],
                'is_active': True,
            }
        )
        
        # Attach placeholder image if new
        if is_new and not service.image:
            img_data = generate_placeholder_image(service_data['title'])
            filename = f"service_{service.id}_{service_data['title'].lower().replace(' ', '_')}.jpg"
            service.image.save(filename, ContentFile(img_data), save=True)
            created += 1
            print(f"Created Service: {service.title}")
        else:
            print(f"Service already exists: {service.title}")
    
    print(f"Total services created: {created}")


if __name__ == '__main__':
    add_services()
