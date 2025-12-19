from django.db import models
from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser, UserManager
from django.utils import timezone
from django.core.exceptions import ValidationError
import random
import string
from urllib.parse import urlparse, parse_qs
from decimal import Decimal


class CustomUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        # Ensure role is set to admin for any superuser created via management commands
        extra_fields.setdefault('role', 'admin')
        return super().create_superuser(username, email=email, password=password, **extra_fields)


class CustomUser(AbstractUser):
    objects = CustomUserManager()
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
    is_favorite = models.BooleanField(default=False)
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
    CATEGORY_TYPES = [
        ('fish', 'Fish'),
        ('combo', 'Combo Offers'),
        ('accessory', 'Accessories'),
        ('plant', 'Plants'),
    ]

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES, default='fish')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category_type', 'name']

    def __str__(self):
        return self.name


class CategoryTypeManager(models.Manager):
    def __init__(self, category_type):
        super().__init__()
        self.category_type = category_type

    def get_queryset(self):
        return super().get_queryset().filter(category_type=self.category_type)


class FishCategory(Category):
    objects = CategoryTypeManager('fish')

    class Meta:
        proxy = True
        verbose_name = 'Fish Category'
        verbose_name_plural = 'Fish Categories'

    def save(self, *args, **kwargs):
        self.category_type = 'fish'
        super().save(*args, **kwargs)


class ComboCategory(Category):
    objects = CategoryTypeManager('combo')

    class Meta:
        proxy = True
        verbose_name = 'Combo Offer Category'
        verbose_name_plural = 'Combo Offer Categories'

    def save(self, *args, **kwargs):
        self.category_type = 'combo'
        super().save(*args, **kwargs)


class AccessoryCategory(Category):
    objects = CategoryTypeManager('accessory')

    class Meta:
        proxy = True
        verbose_name = 'Accessory Category'
        verbose_name_plural = 'Accessory Categories'

    def save(self, *args, **kwargs):
        self.category_type = 'accessory'
        super().save(*args, **kwargs)


class PlantCategory(Category):
    objects = CategoryTypeManager('plant')

    class Meta:
        proxy = True
        verbose_name = 'Plant Category'
        verbose_name_plural = 'Plant Categories'

    def save(self, *args, **kwargs):
        self.category_type = 'plant'
        super().save(*args, **kwargs)


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
    weight = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True, help_text='Average weight in kilograms (optional)')
    stock_quantity = models.IntegerField(default=0)
    minimum_order_quantity = models.IntegerField(default=1, help_text='Minimum quantity required per order')
    image = models.ImageField(upload_to='fishes/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text='If checked, this fish appears in Featured Fishes section')
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    
    def __str__(self):
        return f"{self.name} - {self.breed.name}"
    def __str__(self):
        return f"{self.name} - {self.breed.name}"


class Notification(models.Model):
    LEVEL_CHOICES = (
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    )
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='info')
    # Optional related fish
    fish = models.ForeignKey(Fish, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.level})"


# Signals to create notifications when fish stock changes
@receiver(pre_save, sender=Fish)
def fish_pre_save(sender, instance, **kwargs):
    if not instance.pk:
        instance._previous_stock = None
        return
    try:
        prev = sender.objects.get(pk=instance.pk)
        instance._previous_stock = prev.stock_quantity
    except sender.DoesNotExist:
        instance._previous_stock = None


@receiver(post_save, sender=Fish)
def fish_post_save(sender, instance, created, **kwargs):
    # Only care about updates
    if created:
        return

    prev = getattr(instance, '_previous_stock', None)
    curr = instance.stock_quantity or 0
    threshold = getattr(settings, 'LOW_STOCK_THRESHOLD', 5)

    # Out of stock
    if curr <= 0 and (prev is None or prev > 0):
        # avoid duplicate unread critical notification for same fish
        exists = Notification.objects.filter(fish=instance, level='critical', is_read=False).exists()
        if not exists:
            Notification.objects.create(
                title=f"{instance.name} is out of stock",
                message=f"{instance.name} has run out of stock.",
                level='critical',
                fish=instance,
            )
    # Low stock threshold crossed
    elif curr <= threshold and (prev is None or (prev is not None and prev > threshold)):
        exists = Notification.objects.filter(fish=instance, level='warning', is_read=False).exists()
        if not exists:
            Notification.objects.create(
                title=f"{instance.name} stock is low",
                message=f"{instance.name} stock is low (only {curr} left).",
                level='warning',
                fish=instance,
            )




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
    combo = models.ForeignKey('ComboOffer', on_delete=models.SET_NULL, null=True, blank=True, related_name='cart_items')
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [('user', 'fish', 'combo')]
    
    def __str__(self):
        return f"{self.user.username} - {self.fish.name}"
    
    def get_total(self):
        return self.fish.price * self.quantity


# Combo / bundle models
class ComboOffer(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    bundle_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='combo_offers',
        help_text='Select a combo offer category to help group related bundles.',
    )
    is_active = models.BooleanField(default=True)
    # Whether to show this combo on the homepage or promotional spots.
    # Added to match existing DB schema where this column may already exist.
    show_on_homepage = models.BooleanField(default=False)
    # Optional banner image to display on the homepage as a wide banner
    banner_image = models.ImageField(upload_to='combo_banners/', null=True, blank=True)
    # If true, present this combo as a homepage banner (not as a card in Combo Deals)
    show_as_banner = models.BooleanField(default=False)
    weight = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True, help_text='Total combo weight in kilograms (optional)')
    # Whether to include this combo in the Limited Offers banner/rotation
    # NOTE: `show_in_limited_offers` removed — combos are managed separately and
    # presented only in the dedicated "Combo Deals" section on the homepage.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class ComboItem(models.Model):
    combo = models.ForeignKey(ComboOffer, on_delete=models.CASCADE, related_name='items')
    fish = models.ForeignKey(Fish, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('combo', 'fish')

    def __str__(self):
        return f"{self.combo.title} - {self.fish.name} x{self.quantity}"


class AccessoryCart(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='accessory_cart_items')
    accessory = models.ForeignKey('Accessory', on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'accessory']

    def __str__(self):
        return f"{self.user.username} - {self.accessory.name}"

    def get_total(self):
        return self.accessory.price * self.quantity


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
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_charge = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_weight = models.DecimalField(max_digits=8, decimal_places=3, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='card')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    # Provider's order id (e.g., Stripe PaymentIntent id or other provider id)
    provider_order_id = models.CharField(max_length=200, blank=True, null=True)
    shipping_address = models.TextField(blank=True, null=True)
    shipping_state = models.CharField(max_length=100, blank=True)
    shipping_pincode = models.CharField(max_length=20, blank=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
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

    @property
    def invoice_url(self):
        if self.payment_status != 'paid':
            return None
        from django.conf import settings
        import os
        invoice_path = os.path.join(settings.MEDIA_ROOT, 'invoices', f'invoice-{self.order_number}.pdf')
        if os.path.exists(invoice_path):
            return settings.MEDIA_URL + f'invoices/invoice-{self.order_number}.pdf'
        return None


class ShippingChargeSetting(models.Model):
    key = models.CharField(max_length=32, unique=True, default='default', editable=False)
    kerala_rate = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('60.00'))
    default_rate = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('100.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Shipping Charge Setting'
        verbose_name_plural = 'Shipping Charge Settings'

    def __str__(self):
        return f"Shipping Charges (Kerala: ₹{self.kerala_rate}, Other: ₹{self.default_rate})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    fish = models.ForeignKey(Fish, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.order.order_number} - {self.fish.name}"
    
    def get_total(self):
        return self.price * self.quantity


class OrderAccessoryItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='accessory_items')
    accessory = models.ForeignKey('Accessory', on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.order.order_number} - {self.accessory.name}"

    def get_total(self):
        return self.price * self.quantity


class OrderPlantItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='plant_items')
    plant = models.ForeignKey('Plant', on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.order.order_number} - {self.plant.name}"

    def get_total(self):
        return self.price * self.quantity


class Review(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reviews')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    image = models.ImageField(upload_to='reviews/', blank=True, null=True)
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'order')
        ordering = ['-created_at']

    def __str__(self):
        num = getattr(self.order, 'order_number', 'N/A')
        return f"Order {num} review by {self.user.username} ({self.rating}★)"


class Service(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0, help_text='Lower numbers appear first')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', '-created_at']

    def __str__(self):
        return self.title


class Accessory(models.Model):
    """Accessories that can be sold alongside fishes (e.g., filters, nets, food)."""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='accessories')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    weight = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True, help_text='Weight in kilograms (optional)')
    stock_quantity = models.IntegerField(default=0)
    minimum_order_quantity = models.IntegerField(default=1, help_text='Minimum quantity required per order')
    image = models.ImageField(upload_to='accessories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_accessories')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', '-created_at']

    def __str__(self):
        return self.name


class Plant(models.Model):
    """Aquatic plants grouped by plant categories."""
    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='plants',
        help_text='Select a plant category to organise this plant.',
    )
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    weight = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True, help_text='Weight in kilograms (optional)')
    stock_quantity = models.IntegerField(default=0)
    minimum_order_quantity = models.IntegerField(default=1, help_text='Minimum quantity required per order')
    image = models.ImageField(upload_to='plants/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_plants',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', '-created_at']
        indexes = [
            models.Index(fields=['is_active', 'display_order']),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.category and self.category.category_type != 'plant':
            raise ValidationError({'category': 'Selected category must be a plant category.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


@receiver(pre_save, sender=Plant)
def plant_pre_save(sender, instance, **kwargs):
    if not instance.pk:
        instance._previous_stock = None
        return
    try:
        prev = sender.objects.get(pk=instance.pk)
        instance._previous_stock = prev.stock_quantity
    except sender.DoesNotExist:
        instance._previous_stock = None


@receiver(post_save, sender=Plant)
def plant_post_save(sender, instance, created, **kwargs):
    if created:
        return

    prev = getattr(instance, '_previous_stock', None)
    curr = instance.stock_quantity or 0

    if curr > 0 or (prev is not None and prev <= 0):
        return

    notification_title = f"{instance.name} plant is out of stock"
    exists = Notification.objects.filter(title=notification_title, is_read=False).exists()
    if exists:
        return

    Notification.objects.create(
        title=notification_title,
        message=f"{instance.name} plant stock has reached zero. Please restock promptly.",
        level='critical',
    )


class PlantMedia(models.Model):
    """Gallery media items for a plant."""
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='media')
    image = models.ImageField(upload_to='plants/gallery/')
    title = models.CharField(max_length=150, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', '-created_at']

    def __str__(self):
        return f"{self.plant.name} - {self.title or self.id}"

    @property
    def source(self):
        try:
            return self.image.url
        except Exception:
            return None


class PlantCart(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='plant_cart_items')
    plant = models.ForeignKey('Plant', on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'plant']

    def __str__(self):
        return f"{self.user.username} - {self.plant.name}"

    def get_total(self):
        if not self.plant.price:
            return Decimal('0')
        return self.plant.price * self.quantity


class ContactInfo(models.Model):
    # Address
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)

    # Phones & Emails
    phone_primary = models.CharField(max_length=30, blank=True)
    phone_secondary = models.CharField(max_length=30, blank=True)
    email_support = models.EmailField(blank=True)
    email_sales = models.EmailField(blank=True)

    # Socials
    whatsapp = models.CharField(max_length=50, blank=True, help_text='WhatsApp number with country code (e.g., +911234567890)')
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)

    # Map & Hours
    map_embed_url = models.URLField(blank=True, help_text='Google Maps embed/share URL')
    opening_hours = models.TextField(blank=True, help_text='One entry per line, e.g. Mon-Fri: 9:00 - 18:00')

    # Meta
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)


class BlogPost(models.Model):
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=260, unique=True)
    author = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='blog_posts')
    excerpt = models.TextField(blank=True)
    content = models.TextField()
    image = models.ImageField(upload_to='blog/', blank=True, null=True)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('blog_detail', args=[self.slug])

    class Meta:
        verbose_name = 'Contact Information'
        verbose_name_plural = 'Contact Information'

    def __str__(self):
        base = self.address_line1 or 'Contact Info'
        return f"{base} ({self.city or ''})".strip()


class ContactGalleryMedia(models.Model):
    MEDIA_TYPES = [
        ("image", "Image"),
        ("video", "Video"),
    ]
    contact = models.ForeignKey(ContactInfo, on_delete=models.CASCADE, related_name='gallery_media')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    file = models.FileField(upload_to='contact_gallery/', blank=True, null=True)
    external_url = models.URLField(blank=True, null=True, help_text='Optional external video URL (YouTube/Vimeo)')
    title = models.CharField(max_length=150, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', '-created_at']

    def __str__(self):
        return f"Gallery Media - {self.media_type} - {self.title or self.id}"

    @property
    def is_video(self):
        return self.media_type == 'video'

    @property
    def source(self):
        if self.file:
            try:
                return self.file.url
            except Exception:
                return None
        return self.external_url

    @property
    def embed_url(self):
        # Mirror FishMedia.embed_url logic for known providers
        if self.file:
            try:
                return self.file.url
            except Exception:
                return None

        url = (self.external_url or '').strip()
        if not url:
            return None

        try:
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'
            parsed = urlparse(url)
            host = (parsed.netloc or '').lower()

            if 'youtube.com' in host:
                if parsed.path == '/watch':
                    vid = parse_qs(parsed.query).get('v', [None])[0]
                    if vid:
                        return f"https://www.youtube.com/embed/{vid}"
                elif parsed.path.startswith('/shorts/'):
                    vid = parsed.path.split('/shorts/')[-1].split('/')[0]
                    if vid:
                        return f"https://www.youtube.com/embed/{vid}"
                elif parsed.path.startswith('/embed/'):
                    return url
            if 'youtu.be' in host:
                vid = parsed.path.lstrip('/')
                if vid:
                    return f"https://www.youtube.com/embed/{vid}"

            if 'vimeo.com' in host:
                if 'player.vimeo.com' in host and parsed.path.startswith('/video/'):
                    return url
                vid = parsed.path.lstrip('/').split('/')[0]
                if vid.isdigit():
                    return f"https://player.vimeo.com/video/{vid}"

            return url
        except Exception:
            return url


class Coupon(models.Model):
    COUPON_TYPE_CHOICES = [
        ('all', 'All Users'),
        ('favorites', 'Favorite Users Only'),
        ('normal', 'Normal Users Only'),
    ]
    
    code = models.CharField(max_length=50, unique=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text='Discount percentage (0-100)')
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Maximum discount amount in rupees')
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Minimum order amount to use this coupon')
    coupon_type = models.CharField(max_length=20, choices=COUPON_TYPE_CHOICES, default='all')
    is_active = models.BooleanField(default=True)
    show_in_suggestions = models.BooleanField(default=True, help_text='Show this coupon in checkout suggestions')
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(null=True, blank=True, help_text='Maximum number of times this coupon can be used (leave blank for unlimited)')
    times_used = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='created_coupons')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
# Add coupon control fields and methods
    force_apply = models.BooleanField(default=False, help_text='If set, this coupon bypasses normal validity checks when applied (admin use only)')
    
    def is_valid(self):
        """Check if coupon is currently valid"""
        now = timezone.now()
        
        if not self.is_active:
            return False
        
        # Check if current time is within valid period
        if self.valid_from and now < self.valid_from:
            return False
        
        if self.valid_until and now > self.valid_until:
            return False
        
        # Check usage limit
        if self.usage_limit and self.times_used >= self.usage_limit:
            return False
        
        return True
    
    def can_use(self, user):
        # If force_apply is enabled, allow use regardless of normal checks
        if self.force_apply:
            return True

        if not self.is_valid():
            return False

        # If user is anonymous, treat as not favorite
        is_fav = getattr(user, 'is_favorite', False)
        if self.coupon_type == 'favorites' and not is_fav:
            return False
        if self.coupon_type == 'normal' and is_fav:
            return False
        return True

class LimitedOffer(models.Model):
    """Time-bound marketing offer displayed on landing page with countdown."""
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    discount_text = models.CharField(max_length=80, help_text="Short highlight like 'Save 25%' or 'Flat ₹500 Off'")
    image = models.ImageField(upload_to='offers/', null=True, blank=True, help_text='Optional banner image for the card background')
    bg_color = models.CharField(max_length=7, blank=True, help_text="Optional hex color (e.g. #1e90ff) used when no image")
    fish = models.ForeignKey(Fish, on_delete=models.SET_NULL, null=True, blank=True, related_name='limited_offers', help_text='Optional: Select a fish to redirect users when they click the banner')
    # Scheduling/display fields: re-added so admin can set start/end and visibility
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    show_on_homepage = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.discount_text})"
    def is_current(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_time and self.end_time:
            return self.start_time <= now <= self.end_time
        # If scheduling not set, consider active
        return True

    def remaining_seconds(self):
        now = timezone.now()
        if self.end_time and self.end_time > now:
            return int((self.end_time - now).total_seconds())
        return 0
    
    def get_redirect_url(self):
        """Get the URL to redirect when banner is clicked"""
        if self.fish:
            from django.urls import reverse
            return reverse('fish_detail', args=[self.fish.id])
        from django.urls import reverse
        return reverse('fish_list')

    class Meta:
        ordering = ['-created_at']

    

