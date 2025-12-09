from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile
from store.models import ContactInfo, ContactGalleryMedia


GALLERY_TITLES = [
    "Aquarium Setup",
    "Fish Collection",
    "Tank Maintenance",
    "Customer Visit",
    "Species Display",
    "Breeding Center",
    "Packing Station",
    "Quality Check",
]


def generate_gallery_image(title: str, index: int) -> bytes:
    """Generate a colored placeholder image for gallery."""
    colors = [
        (25, 118, 210),    # blue
        (56, 142, 60),     # green
        (229, 57, 53),     # red
        (251, 140, 0),     # orange
        (103, 58, 183),    # purple
        (0, 150, 136),     # teal
        (244, 67, 54),     # darker red
        (33, 150, 243),    # lighter blue
    ]
    color = colors[index % len(colors)]
    
    img = Image.new('RGB', (800, 600), color)
    draw = ImageDraw.Draw(img)
    
    try:
        font_title = ImageFont.truetype('arial.ttf', 50)
        font_sub = ImageFont.truetype('arial.ttf', 30)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
    
    # Draw title
    tw, th = draw.textbbox((0, 0), title, font=font_title)[2:]
    draw.text(((800 - tw) // 2, (600 - th) // 2 - 60), title, fill=(255, 255, 255), font=font_title)
    
    # Draw subtitle
    subtitle = f"FISHY FRIEND AQUA"
    sw, sh = draw.textbbox((0, 0), subtitle, font=font_sub)[2:]
    draw.text(((800 - sw) // 2, (600 - sh) // 2 + 60), subtitle, fill=(255, 255, 255), font=font_sub)
    
    buf = BytesIO()
    img.save(buf, format='JPEG', quality=85)
    return buf.getvalue()


def add_gallery_images():
    """Create 8 gallery images for contact page."""
    # Ensure contact exists
    contact = ContactInfo.objects.first()
    if not contact:
        print("ContactInfo not found. Create contact info first.")
        return
    
    created = 0
    for idx, title in enumerate(GALLERY_TITLES):
        gallery, is_new = ContactGalleryMedia.objects.get_or_create(
            contact=contact,
            title=title,
            defaults={
                'media_type': 'image',
                'display_order': idx,
            }
        )
        
        # Attach placeholder image if new
        if is_new and not gallery.file:
            img_data = generate_gallery_image(title, idx)
            filename = f"gallery_{gallery.id}_{title.lower().replace(' ', '_')}.jpg"
            gallery.file.save(filename, ContentFile(img_data), save=True)
            created += 1
            print(f"Created Gallery Image: {title}")
        else:
            print(f"Gallery Image already exists: {title}")
    
    print(f"Total gallery images created: {created}")


if __name__ == '__main__':
    add_gallery_images()
