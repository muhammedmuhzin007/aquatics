from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Category, Breed, Fish, Order


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2', 'phone_number', 'address')


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'image']


class BreedForm(forms.ModelForm):
    class Meta:
        model = Breed
        fields = ['name', 'category', 'description']


class FishForm(forms.ModelForm):
    # Use a numeric size field (in inches) on the form; this is a non-model field
    size_inches = forms.DecimalField(required=False, min_value=0, max_digits=6, decimal_places=2,
                                     widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
                                     help_text='Enter size in inches')

    class Meta:
        model = Fish
        # keep model-backed fields here; `size_inches` is an extra form field handled in view logic
        fields = ['name', 'category', 'breed', 'description', 'price', 'stock_quantity', 'image', 'is_available']


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

