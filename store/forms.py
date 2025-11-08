from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Category, Breed, Fish, Order
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
        fields = ['name', 'category', 'breed', 'description', 'price', 'size', 'stock_quantity', 'image', 'is_available']
        widgets = {
            'size': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'e.g., 4.5'}),
        }
        labels = {
            'size': 'Size (inches)',
        }
        help_texts = {
            'size': 'Enter size in inches',
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
    
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False)
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

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

