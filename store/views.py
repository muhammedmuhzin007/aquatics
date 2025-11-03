from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.mail import send_mail
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, Count
from django.conf import settings
from django.utils import timezone
from .models import (
    CustomUser, Category, Breed, Fish, Cart, Order, OrderItem, OTP
)
from .forms import (
    CustomUserCreationForm, CategoryForm, BreedForm, FishForm,
    ProfileEditForm, OrderFilterForm
)
from datetime import timedelta
import openpyxl
from openpyxl.styles import Font, PatternFill
import pandas as pd


# Helper Functions
def is_customer(user):
    return user.is_authenticated and user.role == 'customer'


def is_staff(user):
    return user.is_authenticated and (user.role == 'staff' or user.role == 'admin')


def is_admin(user):
    return user.is_authenticated and user.role == 'admin'


# Authentication Views
def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'customer'
            user.is_active = False  # Inactive until email verified
            user.save()
            
            # Generate OTP
            otp_code = OTP.generate_otp()
            OTP.objects.create(user=user, otp_code=otp_code)
            
            # Send OTP email
            send_mail(
                'Email Verification OTP - AquaFish Store',
                f'Your OTP for email verification is: {otp_code}\n\nThis OTP will expire in 5 minutes.',
                settings.DEFAULT_FROM_EMAIL or 'noreply@aquafishstore.com',
                [user.email],
                fail_silently=False,
            )
            
            messages.success(request, 'Registration successful! Please check your email for OTP verification.')
            return redirect('verify_otp', user_id=user.id)
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'store/register.html', {'form': form})


def verify_otp_view(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        otp_obj = OTP.objects.filter(user=user, is_used=False).order_by('-created_at').first()
        
        if otp_obj and otp_obj.otp_code == otp_code:
            if otp_obj.is_expired():
                messages.error(request, 'OTP has expired. Please request a new one.')
                return redirect('resend_otp', user_id=user.id)
            
            otp_obj.is_used = True
            otp_obj.save()
            user.email_verified = True
            user.is_active = True
            user.save()
            
            messages.success(request, 'Email verified successfully! You can now login.')
            return redirect('login')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
    
    return render(request, 'store/verify_otp.html', {'user': user})


def resend_otp_view(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        otp_code = OTP.generate_otp()
        OTP.objects.create(user=user, otp_code=otp_code)
        
        send_mail(
            'Email Verification OTP - AquaFish Store',
            f'Your OTP for email verification is: {otp_code}\n\nThis OTP will expire in 5 minutes.',
            settings.DEFAULT_FROM_EMAIL or 'noreply@aquafishstore.com',
            [user.email],
            fail_silently=False,
        )
        
        messages.success(request, 'OTP has been resent to your email.')
        return redirect('verify_otp', user_id=user.id)
    
    return render(request, 'store/resend_otp.html', {'user': user})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user:
            if user.is_blocked:
                messages.error(request, 'Your account has been blocked. Please contact admin.')
                return render(request, 'store/login.html')
            
            if not user.email_verified:
                messages.error(request, 'Please verify your email first.')
                return redirect('verify_otp', user_id=user.id)
            
            login(request, user)
            
            # Redirect based on role
            if user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'staff':
                return redirect('staff_dashboard')
            else:
                return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'store/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = CustomUser.objects.filter(email=email).first()
        
        if user:
            if user.role == 'admin':
                messages.error(request, 'Admin users cannot use forgot password. Please contact system administrator.')
                return render(request, 'store/forgot_password.html')
            
            otp_code = OTP.generate_otp()
            OTP.objects.create(user=user, otp_code=otp_code)
            
            send_mail(
                'Password Reset OTP - AquaFish Store',
                f'Your OTP for password reset is: {otp_code}\n\nThis OTP will expire in 5 minutes.',
                settings.DEFAULT_FROM_EMAIL or 'noreply@aquafishstore.com',
                [user.email],
                fail_silently=False,
            )
            
            messages.success(request, 'OTP has been sent to your email.')
            return redirect('reset_password', user_id=user.id)
        else:
            messages.error(request, 'No account found with this email.')
    
    return render(request, 'store/forgot_password.html')


def reset_password_view(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        otp_obj = OTP.objects.filter(user=user, is_used=False).order_by('-created_at').first()
        
        if otp_obj and otp_obj.otp_code == otp_code:
            if otp_obj.is_expired():
                messages.error(request, 'OTP has expired. Please request a new one.')
                return redirect('forgot_password')
            
            if new_password == confirm_password:
                otp_obj.is_used = True
                otp_obj.save()
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password reset successful! Please login with your new password.')
                return redirect('login')
            else:
                messages.error(request, 'Passwords do not match.')
        else:
            messages.error(request, 'Invalid OTP.')
    
    return render(request, 'store/reset_password.html', {'user': user})


# Home/Customer Views
def home_view(request):
    categories = Category.objects.all()[:6]
    fishes = Fish.objects.filter(is_available=True)[:8]
    first_category = Category.objects.first() if Category.objects.exists() else None
    return render(request, 'store/home.html', {
        'categories': categories, 
        'fishes': fishes,
        'first_category': first_category
    })


@login_required
@user_passes_test(is_customer)
def customer_fish_list_view(request):
    fishes = Fish.objects.filter(is_available=True)
    categories = Category.objects.all()
    breeds = Breed.objects.all()
    
    # Search and filter
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    breed_filter = request.GET.get('breed', '')
    
    if search_query:
        fishes = fishes.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(breed__name__icontains=search_query)
        )
    
    if category_filter:
        fishes = fishes.filter(category_id=category_filter)
    
    if breed_filter:
        fishes = fishes.filter(breed_id=breed_filter)
    
    # If AJAX request, return only the rendered grid partial for live search
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render(request, 'store/customer/_fish_grid.html', {'fishes': fishes}).content.decode('utf-8')
        return JsonResponse({'html': html})

    return render(request, 'store/customer/fish_list.html', {
        'fishes': fishes,
        'categories': categories,
        'breeds': breeds,
        'search_query': search_query,
        'category_filter': category_filter,
        'breed_filter': breed_filter,
    })


@login_required
@user_passes_test(is_customer)
def fish_detail_view(request, fish_id):
    fish = get_object_or_404(Fish, id=fish_id, is_available=True)
    return render(request, 'store/customer/fish_detail.html', {'fish': fish})


@login_required
@user_passes_test(is_customer)
def add_to_cart_view(request, fish_id):
    fish = get_object_or_404(Fish, id=fish_id)
    quantity = int(request.POST.get('quantity', 1))
    
    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        fish=fish,
        defaults={'quantity': quantity}
    )
    
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    
    messages.success(request, f'{fish.name} added to cart.')
    return redirect('cart')


@login_required
@user_passes_test(is_customer)
def cart_view(request):
    cart_items = Cart.objects.filter(user=request.user)
    total = sum(item.get_total() for item in cart_items)
    
    return render(request, 'store/customer/cart.html', {
        'cart_items': cart_items,
        'total': total,
    })


@login_required
@user_passes_test(is_customer)
def update_cart_view(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
    else:
        cart_item.delete()
    
    return redirect('cart')


@login_required
@user_passes_test(is_customer)
def remove_from_cart_view(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
    cart_item.delete()
    messages.success(request, 'Item removed from cart.')
    return redirect('cart')


@login_required
@user_passes_test(is_customer)
def checkout_view(request):
    cart_items = Cart.objects.filter(user=request.user)
    
    if not cart_items:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart')
    
    if request.method == 'POST':
        shipping_address = request.POST.get('shipping_address')
        phone_number = request.POST.get('phone_number')
        
        if not shipping_address or not phone_number:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'store/customer/checkout.html', {'cart_items': cart_items})
        
        # Create order
        total_amount = sum(item.get_total() for item in cart_items)
        order = Order.objects.create(
            user=request.user,
            order_number=Order.generate_order_number(),
            total_amount=total_amount,
            shipping_address=shipping_address,
            phone_number=phone_number,
        )
        
        # Create order items
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                fish=cart_item.fish,
                quantity=cart_item.quantity,
                price=cart_item.fish.price,
            )
            # Update stock
            cart_item.fish.stock_quantity -= cart_item.quantity
            cart_item.fish.save()
        
        # Clear cart
        cart_items.delete()
        
        messages.success(request, f'Order placed successfully! Order number: {order.order_number}')
        return redirect('order_detail', order_id=order.id)
    
    total = sum(item.get_total() for item in cart_items)
    return render(request, 'store/customer/checkout.html', {
        'cart_items': cart_items,
        'total': total,
    })


@login_required
@user_passes_test(is_customer)
def customer_orders_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/customer/orders.html', {'orders': orders})


@login_required
@user_passes_test(is_customer)
def order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/customer/order_detail.html', {'order': order})


# Staff Views
@login_required
@user_passes_test(is_staff)
def staff_dashboard_view(request):
    total_fishes = Fish.objects.count()
    total_categories = Category.objects.count()
    total_breeds = Breed.objects.count()
    total_orders = Order.objects.count()
    
    return render(request, 'store/staff/dashboard.html', {
        'total_fishes': total_fishes,
        'total_categories': total_categories,
        'total_breeds': total_breeds,
        'total_orders': total_orders,
    })


@login_required
@user_passes_test(is_staff)
def staff_fish_list_view(request):
    fishes = Fish.objects.all()
    
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    breed_filter = request.GET.get('breed', '')
    
    if search_query:
        fishes = fishes.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    if category_filter:
        fishes = fishes.filter(category_id=category_filter)
    
    if breed_filter:
        fishes = fishes.filter(breed_id=breed_filter)
    
    categories = Category.objects.all()
    breeds = Breed.objects.all()
    
    return render(request, 'store/staff/fish_list.html', {
        'fishes': fishes,
        'categories': categories,
        'breeds': breeds,
        'search_query': search_query,
        'category_filter': category_filter,
        'breed_filter': breed_filter,
    })


@login_required
@user_passes_test(is_staff)
def add_category_view(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added successfully.')
            return redirect('staff_categories')
    else:
        form = CategoryForm()
    
    return render(request, 'store/staff/add_category.html', {'form': form})


@login_required
@user_passes_test(is_staff)
def staff_categories_view(request):
    categories = Category.objects.all()
    return render(request, 'store/staff/categories.html', {'categories': categories})


@login_required
@user_passes_test(is_staff)
def delete_category_view(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category.delete()
    messages.success(request, 'Category deleted successfully.')
    return redirect('staff_categories')


@login_required
@user_passes_test(is_staff)
def add_breed_view(request):
    if request.method == 'POST':
        form = BreedForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Breed added successfully.')
            return redirect('staff_breeds')
    else:
        form = BreedForm()
    
    categories = Category.objects.all()
    return render(request, 'store/staff/add_breed.html', {'form': form, 'categories': categories})


@login_required
@user_passes_test(is_staff)
def staff_breeds_view(request):
    breeds = Breed.objects.all()
    return render(request, 'store/staff/breeds.html', {'breeds': breeds})


@login_required
@user_passes_test(is_staff)
def delete_breed_view(request, breed_id):
    breed = get_object_or_404(Breed, id=breed_id)
    breed.delete()
    messages.success(request, 'Breed deleted successfully.')
    return redirect('staff_breeds')


@login_required
@user_passes_test(is_staff)
def add_fish_view(request):
    if request.method == 'POST':
        # Check if this is a breed creation request
        if 'create_breed' in request.POST:
            breed_form = BreedForm(request.POST)
            if breed_form.is_valid():
                new_breed = breed_form.save()
                # Return JSON response for AJAX
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'breed_id': new_breed.id,
                        'breed_name': new_breed.name,
                        'message': 'Breed created successfully!'
                    })
                messages.success(request, 'Breed created successfully.')
        
        # Normal fish creation
        form = FishForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fish added successfully.')
            return redirect('staff_fish_list')
    else:
        form = FishForm()
    
    breed_form = BreedForm()
    categories = Category.objects.all()
    breeds = Breed.objects.all()
    return render(request, 'store/staff/add_fish.html', {
        'form': form,
        'breed_form': breed_form,
        'categories': categories,
        'breeds': breeds,
    })


@login_required
@user_passes_test(is_staff)
def edit_fish_view(request, fish_id):
    fish = get_object_or_404(Fish, id=fish_id)
    
    if request.method == 'POST':
        # Check if this is a breed creation request
        if 'create_breed' in request.POST:
            breed_form = BreedForm(request.POST)
            if breed_form.is_valid():
                new_breed = breed_form.save()
                # Return JSON response for AJAX
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'breed_id': new_breed.id,
                        'breed_name': new_breed.name,
                        'message': 'Breed created successfully!'
                    })
                messages.success(request, 'Breed created successfully.')
        
        # Normal fish update
        form = FishForm(request.POST, request.FILES, instance=fish)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fish updated successfully.')
            return redirect('staff_fish_list')
    else:
        form = FishForm(instance=fish)
    
    breed_form = BreedForm()
    categories = Category.objects.all()
    breeds = Breed.objects.all()
    return render(request, 'store/staff/edit_fish.html', {
        'form': form,
        'breed_form': breed_form,
        'fish': fish,
        'categories': categories,
        'breeds': breeds,
    })


@login_required
@user_passes_test(is_staff)
def delete_fish_view(request, fish_id):
    fish = get_object_or_404(Fish, id=fish_id)
    fish.delete()
    messages.success(request, 'Fish deleted successfully.')
    return redirect('staff_fish_list')


# Admin Views
@login_required
@user_passes_test(is_admin)
def admin_dashboard_view(request):
    total_users = CustomUser.objects.filter(role='customer').count()
    total_staff = CustomUser.objects.filter(role='staff').count()
    total_orders = Order.objects.count()
    total_revenue = Order.objects.filter(status='delivered').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    recent_orders = Order.objects.all().order_by('-created_at')[:5]
    
    # Get data for charts
    # Last 6 months of data
    from django.utils import timezone
    six_months_ago = timezone.now() - timedelta(days=180)
    
    # Monthly orders data
    monthly_orders = (Order.objects
        .filter(created_at__gte=six_months_ago)
        .values('created_at__year', 'created_at__month')
        .annotate(count=Count('id'))
        .order_by('created_at__year', 'created_at__month'))
    
    # Monthly revenue data
    monthly_revenue = (Order.objects
        .filter(created_at__gte=six_months_ago, status='delivered')
        .values('created_at__year', 'created_at__month')
        .annotate(total=Sum('total_amount'))
        .order_by('created_at__year', 'created_at__month'))
    
    # Convert month strings to datetime for proper formatting
    months = []
    orders_data = []
    revenue_data = []
    
    # Create a mapping of previous 6 months
    month_data = {}
    current = timezone.now()
    for i in range(6):
        month_key = (current.year, current.month)
        month_data[month_key] = {
            'month_name': current.strftime('%B %Y'),
            'orders': 0,
            'revenue': 0
        }
        # Go to previous month
        if current.month == 1:
            current = current.replace(year=current.year-1, month=12, day=1)
        else:
            current = current.replace(month=current.month-1, day=1)
    
    # Fill in actual data
    for entry in monthly_orders:
        month_key = (entry['created_at__year'], entry['created_at__month'])
        if month_key in month_data:
            month_data[month_key]['orders'] = entry['count']
    
    for entry in monthly_revenue:
        month_key = (entry['created_at__year'], entry['created_at__month'])
        if month_key in month_data:
            month_data[month_key]['revenue'] = float(entry['total'] if entry['total'] else 0)
    
    # Convert to lists for the template
    sorted_months = sorted(month_data.keys(), reverse=True)  # Most recent first
    for month_key in sorted_months:
        months.append(month_data[month_key]['month_name'])
        orders_data.append(month_data[month_key]['orders'])
        revenue_data.append(month_data[month_key]['revenue'])
    
    return render(request, 'store/admin/dashboard.html', {
        'total_users': total_users,
        'total_staff': total_staff,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'chart_months': months,
        'chart_orders': orders_data,
        'chart_revenue': revenue_data,
    })


@login_required
@user_passes_test(is_admin)
def admin_staff_list_view(request):
    staff_members = CustomUser.objects.filter(role='staff')
    return render(request, 'store/admin/staff_list.html', {'staff_members': staff_members})


@login_required
@user_passes_test(is_admin)
def add_staff_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'staff'
            user.email_verified = True
            user.is_active = True
            user.save()
            messages.success(request, 'Staff member added successfully.')
            return redirect('admin_staff_list')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'store/admin/add_staff.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def remove_staff_view(request, user_id):
    staff = get_object_or_404(CustomUser, id=user_id, role='staff')
    staff.delete()
    messages.success(request, 'Staff member removed successfully.')
    return redirect('admin_staff_list')


@login_required
@user_passes_test(is_admin)
def admin_categories_view(request):
    categories = Category.objects.all()
    return render(request, 'store/admin/categories.html', {'categories': categories})


@login_required
@user_passes_test(is_admin)
def admin_add_category_view(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added successfully.')
            return redirect('admin_categories')
    else:
        form = CategoryForm()
    
    return render(request, 'store/admin/add_category.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def admin_delete_category_view(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category.delete()
    messages.success(request, 'Category deleted successfully.')
    return redirect('admin_categories')


@login_required
@user_passes_test(is_admin)
def admin_breeds_view(request):
    breeds = Breed.objects.all()
    return render(request, 'store/admin/breeds.html', {'breeds': breeds})


@login_required
@user_passes_test(is_admin)
def admin_add_breed_view(request):
    if request.method == 'POST':
        form = BreedForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Breed added successfully.')
            return redirect('admin_breeds')
    else:
        form = BreedForm()
    
    categories = Category.objects.all()
    return render(request, 'store/admin/add_breed.html', {'form': form, 'categories': categories})


@login_required
@user_passes_test(is_admin)
def admin_delete_breed_view(request, breed_id):
    breed = get_object_or_404(Breed, id=breed_id)
    breed.delete()
    messages.success(request, 'Breed deleted successfully.')
    return redirect('admin_breeds')


@login_required
@user_passes_test(is_admin)
def admin_fishes_view(request):
    fishes = Fish.objects.all()
    return render(request, 'store/admin/fishes.html', {'fishes': fishes})


@login_required
@user_passes_test(is_admin)
def admin_add_fish_view(request):
    if request.method == 'POST':
        # Check if this is a breed creation request
        if 'create_breed' in request.POST:
            breed_form = BreedForm(request.POST)
            if breed_form.is_valid():
                new_breed = breed_form.save()
                # Return JSON response for AJAX
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'breed_id': new_breed.id,
                        'breed_name': new_breed.name,
                        'message': 'Breed created successfully!'
                    })
                messages.success(request, 'Breed created successfully.')
        
        # Normal fish creation
        form = FishForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fish added successfully.')
            return redirect('admin_fishes')
    else:
        form = FishForm()
    
    breed_form = BreedForm()
    categories = Category.objects.all()
    breeds = Breed.objects.all()
    return render(request, 'store/admin/add_fish.html', {
        'form': form,
        'breed_form': breed_form,
        'categories': categories,
        'breeds': breeds,
    })


@login_required
@user_passes_test(is_admin)
def admin_delete_fish_view(request, fish_id):
    fish = get_object_or_404(Fish, id=fish_id)
    fish.delete()
    messages.success(request, 'Fish deleted successfully.')
    return redirect('admin_fishes')


@login_required
@user_passes_test(is_admin)
def admin_orders_view(request):
    orders = Order.objects.all().order_by('-created_at')
    
    # Filter
    form = OrderFilterForm(request.GET)
    if form.is_valid():
        status = form.cleaned_data.get('status')
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        
        if status:
            orders = orders.filter(status=status)
        
        if start_date:
            orders = orders.filter(created_at__gte=start_date)
        
        if end_date:
            orders = orders.filter(created_at__lte=end_date)
    
    return render(request, 'store/admin/orders.html', {
        'orders': orders,
        'form': form,
    })


@login_required
@user_passes_test(is_admin)
def admin_order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'store/admin/order_detail.html', {'order': order})


@login_required
@user_passes_test(is_admin)
def admin_users_view(request):
    users = CustomUser.objects.filter(role='customer')
    return render(request, 'store/admin/users.html', {'users': users})


@login_required
@user_passes_test(is_admin)
def block_user_view(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id, role='customer')
    user.is_blocked = True
    user.save()
    messages.success(request, f'User {user.username} has been blocked.')
    return redirect('admin_users')


@login_required
@user_passes_test(is_admin)
def unblock_user_view(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id, role='customer')
    user.is_blocked = False
    user.save()
    messages.success(request, f'User {user.username} has been unblocked.')
    return redirect('admin_users')


@login_required
@user_passes_test(is_admin)
def export_orders_excel_view(request):
    orders = Order.objects.all().order_by('-created_at')
    
    # Filter
    status = request.GET.get('status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if status:
        orders = orders.filter(status=status)
    if start_date:
        orders = orders.filter(created_at__gte=start_date)
    if end_date:
        orders = orders.filter(created_at__lte=end_date)
    
    # Create Excel workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Orders"
    
    # Header
    headers = ['Order Number', 'User', 'Total Amount', 'Status', 'Shipping Address', 'Phone', 'Date']
    ws.append(headers)
    
    # Style header
    header_fill = PatternFill(start_color="0066CC", end_color="0066CC", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
    
    # Data
    for order in orders:
        ws.append([
            order.order_number,
            order.user.username,
            float(order.total_amount),
            order.status,
            order.shipping_address,
            order.phone_number,
            order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])
    
    # Response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="orders.xlsx"'
    wb.save(response)
    return response


# Profile Views
@login_required
def profile_view(request):
    return render(request, 'store/profile.html', {'user': request.user})


@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = ProfileEditForm(instance=request.user)
    
    return render(request, 'store/edit_profile.html', {'form': form})

