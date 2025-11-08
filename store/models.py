from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import random
import string
from urllib.parse import urlparse, parse_qs


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('staff', 'Staff'),
        ('admin', 'Admin'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_blocked = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.username} ({self.role})"


class OTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    def __str__(self):
        return f"OTP for {self.user.email}"
    
    @staticmethod
    def generate_otp():
        return ''.join(random.choices(string.digits, k=6))
    
    def is_expired(self):
        return (timezone.now() - self.created_at).seconds > 300  # 5 minutes


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class Breed(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='breeds')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['name', 'category']
    
    def __str__(self):
        return f"{self.name} ({self.category.name})"


class Fish(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='fishes')
    breed = models.ForeignKey(Breed, on_delete=models.CASCADE, related_name='fishes')
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    size = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text='Size in inches')
    stock_quantity = models.IntegerField(default=0)
    image = models.ImageField(upload_to='fishes/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.breed.name}"


class FishMedia(models.Model):
    MEDIA_TYPES = [
        ("image", "Image"),
        ("video", "Video"),
    ]
    fish = models.ForeignKey(Fish, on_delete=models.CASCADE, related_name="media")
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    file = models.FileField(upload_to="fishes/media/", blank=True, null=True)
    external_url = models.URLField(blank=True, null=True, help_text="Optional external video URL (e.g., YouTube)")
    title = models.CharField(max_length=150, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["display_order", "-created_at"]

    def __str__(self):
        return f"{self.fish.name} - {self.media_type} - {self.title or self.id}"

    @property
    def is_video(self):
        return self.media_type == "video"

    @property
    def source(self):
        """Return a usable URL for the media (file or external)."""
        if self.file:
            try:
                return self.file.url
            except Exception:
                return None
        return self.external_url

    @property
    def embed_url(self):
        """Return an embeddable URL for known providers (YouTube/Vimeo). Falls back to source."""
        if self.file:
            # For uploaded videos/images, use the direct file URL
            try:
                return self.file.url
            except Exception:
                return None

        url = (self.external_url or '').strip()
        if not url:
            return None

        try:
            # Ensure scheme present; user may paste 'www.youtube.com/watch?v=ID'
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'
            parsed = urlparse(url)
            host = (parsed.netloc or '').lower()

            # YouTube variants
            if 'youtube.com' in host:
                # formats like /watch?v=VIDEO_ID or /shorts/VIDEO_ID
                if parsed.path == '/watch':
                    vid = parse_qs(parsed.query).get('v', [None])[0]
                    if vid:
                        return f"https://www.youtube.com/embed/{vid}"
                elif parsed.path.startswith('/shorts/'):
                    vid = parsed.path.split('/shorts/')[-1].split('/')[0]
                    if vid:
                        return f"https://www.youtube.com/embed/{vid}"
                elif parsed.path.startswith('/embed/'):
                    return url  # already embed format
            if 'youtu.be' in host:
                # format: https://youtu.be/VIDEO_ID
                vid = parsed.path.lstrip('/')
                if vid:
                    return f"https://www.youtube.com/embed/{vid}"

            # Vimeo
            if 'vimeo.com' in host:
                # format: https://vimeo.com/VIDEO_ID or player.vimeo.com/video/VIDEO_ID
                if 'player.vimeo.com' in host and parsed.path.startswith('/video/'):
                    return url  # already embed
                vid = parsed.path.lstrip('/').split('/')[0]
                if vid.isdigit():
                    return f"https://player.vimeo.com/video/{vid}"

            # Unknown provider - return original URL
            return url
        except Exception:
            # On any parsing error, return the original
            return url


class Cart(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='cart_items')
    fish = models.ForeignKey(Fish, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'fish']
    
    def __str__(self):
        return f"{self.user.username} - {self.fish.name}"
    
    def get_total(self):
        return self.fish.price * self.quantity


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('upi', 'UPI Payment'),
        ('netbanking', 'Net Banking'),
        ('wallet', 'Digital Wallet'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='card')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    shipping_address = models.TextField()
    phone_number = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order {self.order_number} - {self.user.username}"
    
    @staticmethod
    def generate_order_number():
        while True:
            order_number = f"ORD{random.randint(100000, 999999)}"
            if not Order.objects.filter(order_number=order_number).exists():
                return order_number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    fish = models.ForeignKey(Fish, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.order.order_number} - {self.fish.name}"
    
    def get_total(self):
        return self.price * self.quantity

