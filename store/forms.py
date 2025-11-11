from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Category, Breed, Fish, Order, Review, Service, ContactInfo, Coupon, LimitedOffer
from .models import FishMedia


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2', 'phone_number', 'address')


class StaffCreateForm(forms.ModelForm):
    """Staff creation form without password fields. Password will be set via OTP/reset flow."""
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone_number', 'address', 'first_name', 'last_name')


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'image']


class BreedForm(forms.ModelForm):
    class Meta:
        model = Breed
        fields = ['name', 'category', 'description']


class FishForm(forms.ModelForm):
    class Meta:
        model = Fish
        fields = ['name', 'category', 'breed', 'description', 'price', 'size', 'stock_quantity', 'minimum_order_quantity', 'image', 'is_available', 'is_featured']
        widgets = {
            'size': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'e.g., 4.5'}),
            'minimum_order_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'e.g., 1'}),
        }
        labels = {
            'size': 'Size (inches)',
            'minimum_order_quantity': 'Minimum Order Quantity',
            'is_featured': 'Featured',
        }
        help_texts = {
            'size': 'Enter size in inches',
            'minimum_order_quantity': 'Minimum quantity required per order',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize breed choices to show category in parentheses
        if 'breed' in self.fields:
            self.fields['breed'].queryset = Breed.objects.select_related('category').all()
            self.fields['breed'].label_from_instance = lambda obj: f"{obj.name} ({obj.category.name})"


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'address', 'profile_picture']


class OrderFilterForm(forms.Form):
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control datepicker', 'placeholder': 'YYYY-MM-DD', 'autocomplete': 'off'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control datepicker', 'placeholder': 'YYYY-MM-DD', 'autocomplete': 'off'})
    )

class FishMediaForm(forms.ModelForm):
    class Meta:
        model = FishMedia
        fields = ['media_type', 'file', 'external_url', 'title', 'display_order']
        widgets = {
            'media_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional title'}),
            'external_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'YouTube/Vimeo URL (optional)'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
        labels = {
            'media_type': 'Type',
            'file': 'Upload File (image/video)',
            'external_url': 'External Video URL',
            'display_order': 'Order',
        }


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Current password'}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New password'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'}))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old = self.cleaned_data.get('old_password')
        if not self.user.check_password(old):
            raise forms.ValidationError('Current password is incorrect.')
        return old

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('new_password1')
        p2 = cleaned.get('new_password2')
        old = cleaned.get('old_password')
        if p1 and p2 and p1 != p2:
            self.add_error('new_password2', 'New passwords do not match.')
        if p1 and old and p1 == old:
            self.add_error('new_password1', 'New password cannot be the same as the old password.')
        # Basic strength checks
        if p1 and len(p1) < 8:
            self.add_error('new_password1', 'Password must be at least 8 characters long.')
        if p1 and self.user.username.lower() in p1.lower():
            self.add_error('new_password1', 'Password is too similar to your username.')
        if p1 and self.user.email and self.user.email.split('@')[0].lower() in p1.lower():
            self.add_error('new_password1', 'Password is too similar to parts of your email.')
        return cleaned

    def save(self, commit=True):
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Share your experience (optional)'}),
        }
        labels = {
            'rating': 'Rating (1-5 Stars)',
            'comment': 'Review Comment',
        }


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['title', 'description', 'icon', 'image', 'is_active', 'display_order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Service title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the service'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. fas fa-fish'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
        labels = {
            'icon': 'Font Awesome Icon',
            'is_active': 'Active',
            'display_order': 'Order',
        }


class ContactInfoForm(forms.ModelForm):
    class Meta:
        model = ContactInfo
        fields = [
            'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country',
            'phone_primary', 'phone_secondary', 'email_support', 'email_sales',
            'whatsapp', 'facebook_url', 'instagram_url', 'twitter_url', 'youtube_url',
            'map_embed_url', 'opening_hours'
        ]
        widgets = {
            'address_line1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address line 1'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address line 2'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_primary': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 12345 67890'}),
            'phone_secondary': forms.TextInput(attrs={'class': 'form-control'}),
            'email_support': forms.EmailInput(attrs={'class': 'form-control'}),
            'email_sales': forms.EmailInput(attrs={'class': 'form-control'}),
            'whatsapp': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+911234567890'}),
            'facebook_url': forms.URLInput(attrs={'class': 'form-control'}),
            'instagram_url': forms.URLInput(attrs={'class': 'form-control'}),
            'twitter_url': forms.URLInput(attrs={'class': 'form-control'}),
            'youtube_url': forms.URLInput(attrs={'class': 'form-control'}),
            'map_embed_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://www.google.com/maps/embed?...'}),
            'opening_hours': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Mon–Fri: 09:00–18:00\nSat: 10:00–14:00'}),
        }
        labels = {
            'map_embed_url': 'Google Maps Embed URL',
            'opening_hours': 'Opening Hours',
        }


class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['code', 'discount_percentage', 'max_discount_amount', 'min_order_amount', 
                  'coupon_type', 'is_active', 'show_in_suggestions', 'valid_from', 'valid_until', 'usage_limit']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., SAVE20', 'style': 'text-transform: uppercase;'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'max_discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Optional'}),
            'min_order_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'coupon_type': forms.Select(attrs={'class': 'form-select custom-select-icon'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_in_suggestions': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'valid_from': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'valid_until': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'usage_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'Leave blank for unlimited'}),
        }
        labels = {
            'code': 'Coupon Code',
            'discount_percentage': 'Discount Percentage (%)',
            'max_discount_amount': 'Maximum Discount Amount (₹)',
            'min_order_amount': 'Minimum Order Amount (₹)',
            'coupon_type': 'User Type',
            'is_active': 'Active',
            'show_in_suggestions': 'Show in Checkout Suggestions',
            'valid_from': 'Valid From',
            'valid_until': 'Valid Until',
            'usage_limit': 'Usage Limit',
        }

class LimitedOfferForm(forms.ModelForm):
    start_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}))
    end_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}))
    class Meta:
        model = LimitedOffer
        fields = ['title', 'description', 'discount_text', 'image', 'bg_color', 'fish', 'start_time', 'end_time', 'is_active', 'show_on_homepage']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'discount_text': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'bg_color': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color'}),
            'fish': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_on_homepage': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'title': 'Offer Title',
            'description': 'Details',
            'discount_text': 'Discount Highlight',
            'image': 'Banner Image (optional)',
            'bg_color': 'Background Color (fallback)',
            'fish': 'Select Fish (optional)',
            'start_time': 'Starts At',
            'end_time': 'Ends At',
            'is_active': 'Active',
            'show_on_homepage': 'Show on Landing Page',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize fish choices to show name and breed
        if 'fish' in self.fields:
            self.fields['fish'].queryset = Fish.objects.select_related('breed', 'category').filter(is_available=True)
            self.fields['fish'].label_from_instance = lambda obj: f"{obj.name} - {obj.breed.name} ({obj.category.name})"
            self.fields['fish'].empty_label = "-- No specific fish (general offer) --"
