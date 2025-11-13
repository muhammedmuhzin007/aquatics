from .models import CustomUser, Category, Breed, Fish, Order, OrderItem, Review, Service, ContactInfo, Coupon, LimitedOffer
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.mail import send_mail
from django.http import JsonResponse, HttpResponse
from django.db import models
from django.db.models import Q, Sum, Count
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import update_session_auth_hash
from django.utils import timezone
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import (
    CustomUser, Category, Breed, Fish, FishMedia, Cart, AccessoryCart, Order, OrderItem, OrderAccessoryItem, OTP, Review, Service, ContactInfo, Coupon, Accessory
)
from .forms import (
    CustomUserCreationForm, StaffCreateForm, CategoryForm, BreedForm, FishForm, FishMediaForm,
    ProfileEditForm, OrderFilterForm, ChangePasswordForm, ReviewForm, ServiceForm, ContactInfoForm, CouponForm,
    LimitedOfferForm
)
from urllib.parse import quote_plus
from datetime import timedelta
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
import pandas as pd
import qrcode
from io import BytesIO
import base64
import uuid
import smtplib
import socket


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
            # Do not create user yet; store form data in session
            data = {
                'username': form.cleaned_data.get('username'),
                'email': form.cleaned_data.get('email'),
                'password1': form.cleaned_data.get('password1'),
                'first_name': form.cleaned_data.get('first_name', ''),
                'last_name': form.cleaned_data.get('last_name', ''),
            }
            request.session['pending_registration'] = data

            # Generate OTP for email verification (session-based)
            otp_code = OTP.generate_otp()
            request.session['pending_registration_otp'] = otp_code
            request.session['pending_registration_time'] = timezone.now().isoformat()

            # Send OTP email
            send_mail(
                f'Email Verification OTP - {settings.SITE_NAME}',
                f"Your OTP for email verification is: {otp_code}\n\nThis OTP will expire in 5 minutes.",
                settings.DEFAULT_FROM_EMAIL or 'noreply@aquafishstore.com',
                [data['email']],
                fail_silently=False,
            )

            messages.success(request, 'We\'ve sent an OTP to your email. Please verify to complete registration.')
            return redirect('verify_otp')
    else:
        form = CustomUserCreationForm()

    return render(request, 'store/register.html', {'form': form})


def verify_otp_view(request):
    # Registration OTP verification using session
    pending = request.session.get('pending_registration')
    if not pending:
        messages.error(request, 'No registration in progress. Please register first.')
        return redirect('register')

    pending_email = pending.get('email')
    created_iso = request.session.get('pending_registration_time')
    try:
        created_at = timezone.datetime.fromisoformat(created_iso) if created_iso else None
        if created_at and timezone.is_naive(created_at):
            created_at = timezone.make_aware(created_at, timezone.get_current_timezone())
    except Exception:
        created_at = None

    if request.method == 'POST':
        otp_code = (request.POST.get('otp_code') or '').strip()
        session_otp = request.session.get('pending_registration_otp')

        # Expiry check: 5 minutes
        is_expired = False
        if created_at:
            delta = timezone.now() - created_at
            is_expired = delta.total_seconds() > 300

        if is_expired:
            messages.error(request, 'OTP has expired. Please request a new one.')
            return redirect('resend_otp')

        if session_otp and otp_code == session_otp:
            # Create user now
            username = pending.get('username')
            email = pending.get('email')
            password = pending.get('password1')
            first_name = pending.get('first_name', '')
            last_name = pending.get('last_name', '')

            if CustomUser.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists. Please register again with a different username.')
                # Clear pending session
                for k in ['pending_registration', 'pending_registration_otp', 'pending_registration_time']:
                    request.session.pop(k, None)
                return redirect('register')
            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, 'Email already registered. Try logging in or reset your password.')
                for k in ['pending_registration', 'pending_registration_otp', 'pending_registration_time']:
                    request.session.pop(k, None)
                return redirect('login')

            user = CustomUser(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role='customer',
                is_active=True,
                email_verified=True,
            )
            user.set_password(password)
            user.save()

            # Clear pending session
            for k in ['pending_registration', 'pending_registration_otp', 'pending_registration_time']:
                request.session.pop(k, None)

            messages.success(request, 'Email verified and account created successfully! You can now login.')
            return redirect('login')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')

    return render(request, 'store/verify_otp.html', {'pending_email': pending_email})


def resend_otp_view(request):
    pending = request.session.get('pending_registration')
    if not pending:
        messages.error(request, 'No registration in progress. Please register first.')
        return redirect('register')

    if request.method == 'POST':
        otp_code = OTP.generate_otp()
        request.session['pending_registration_otp'] = otp_code
        request.session['pending_registration_time'] = timezone.now().isoformat()

        send_mail(
            f'Email Verification OTP - {settings.SITE_NAME}',
            f"Your OTP for email verification is: {otp_code}\n\nThis OTP will expire in 5 minutes.",
            settings.DEFAULT_FROM_EMAIL or 'noreply@aquafishstore.com',
            [pending.get('email')],
            fail_silently=False,
        )

        messages.success(request, 'A new OTP has been sent to your email.')
        return redirect('verify_otp')

    return render(request, 'store/resend_otp.html', {'pending_email': pending.get('email')})


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
                # Registration OTP flow is session-based; just send the user to verification page.
                # Note: If there's no pending registration session, the page will prompt them to register again.
                return redirect('verify_otp')
            
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


def test_email_view(request):
    """DEBUG-only endpoint to test email delivery.
    Usage: /test-email/?to=address@example.com
    Sends a simple email and returns backend info or error details.
    """
    if not settings.DEBUG:
        return HttpResponse(status=404)
    to_addr = request.GET.get('to') or (request.user.email if request.user.is_authenticated else None)
    if not to_addr:
        return HttpResponse("Provide ?to=email@example.com or login with an email.", status=400)
    try:
        send_mail(
            f'{settings.SITE_NAME} - Test Email',
            f'This is a test email from {settings.SITE_NAME}. If you received this, SMTP is configured correctly.',
            settings.DEFAULT_FROM_EMAIL or 'noreply@aquafishstore.local',
            [to_addr],
            fail_silently=False,
        )
        return HttpResponse(f"Sent test email to {to_addr} using backend {settings.EMAIL_BACKEND}.")
    except Exception as e:
        return HttpResponse(f"Email send error: {e}", status=500)


def email_config_view(request):
    """DEBUG diagnostic: shows current email settings and attempts SMTP connectivity."""
    if not settings.DEBUG:
        return HttpResponse(status=404)
    info = {
        'EMAIL_BACKEND': settings.EMAIL_BACKEND,
        'EMAIL_HOST': getattr(settings, 'EMAIL_HOST', None),
        'EMAIL_PORT': getattr(settings, 'EMAIL_PORT', None),
        'EMAIL_USE_TLS': getattr(settings, 'EMAIL_USE_TLS', None),
        'EMAIL_USE_SSL': getattr(settings, 'EMAIL_USE_SSL', None),
        'EMAIL_HOST_USER': getattr(settings, 'EMAIL_HOST_USER', None),
        'DEFAULT_FROM_EMAIL': settings.DEFAULT_FROM_EMAIL,
        'EMAIL_TIMEOUT': getattr(settings, 'EMAIL_TIMEOUT', None),
    }
    connectivity = 'skip (console backend)'
    error = None
    if info['EMAIL_BACKEND'] != 'django.core.mail.backends.console.EmailBackend' and info['EMAIL_HOST'] and info['EMAIL_PORT']:
        try:
            if info['EMAIL_USE_SSL']:
                server = smtplib.SMTP_SSL(host=info['EMAIL_HOST'], port=info['EMAIL_PORT'], timeout=info['EMAIL_TIMEOUT'])
            else:
                server = smtplib.SMTP(host=info['EMAIL_HOST'], port=info['EMAIL_PORT'], timeout=info['EMAIL_TIMEOUT'])
                if info['EMAIL_USE_TLS']:
                    server.starttls()
            server.quit()
            connectivity = 'ok'
        except (socket.error, smtplib.SMTPException) as e:
            connectivity = 'fail'
            error = str(e)

    html = ["<h2>Email Configuration Diagnostic</h2>"]
    html.append("<table border='1' cellpadding='5' style='border-collapse:collapse;font-family:monospace;'>")
    for k, v in info.items():
        html.append(f"<tr><th>{k}</th><td>{v}</td></tr>")
    html.append(f"<tr><th>SMTP Connectivity</th><td>{connectivity}</td></tr>")
    if error:
        html.append(f"<tr><th>Error</th><td style='color:red'>{error}</td></tr>")
    html.append("</table>")
    html.append("<p>Use /test-email/?to=address to send a test message.</p>")
    return HttpResponse(''.join(html))


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
                f'Password Reset OTP - {settings.SITE_NAME}',
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
    fishes = Fish.objects.filter(is_available=True, is_featured=True)[:8]
    # Limited offers currently active and marked to show on homepage
    now = timezone.now()
    limited_offers = LimitedOffer.objects.filter(
        is_active=True,
        show_on_homepage=True,
        start_time__lte=now,
        end_time__gte=now,
    ).order_by('end_time')[:4]
    first_category = Category.objects.first() if Category.objects.exists() else None
    reviews = (Review.objects.filter(approved=True)
               .select_related('order', 'user')
               .prefetch_related('order__items', 'order__items__fish')[:10])
    return render(request, 'store/home.html', {
        'categories': categories, 
        'fishes': fishes,
        'first_category': first_category,
        'reviews': reviews,
        'limited_offers': list(limited_offers),
    })

@login_required
@user_passes_test(is_admin)
def admin_limited_offers_view(request):
    offers = LimitedOffer.objects.all().order_by('-created_at')
    return render(request, 'store/admin/limited_offers.html', {'offers': offers})

@login_required
@user_passes_test(is_admin)
def admin_add_limited_offer_view(request):
    if request.method == 'POST':
        form = LimitedOfferForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Limited offer created successfully.')
            return redirect('admin_limited_offers')
    else:
        form = LimitedOfferForm()
    return render(request, 'store/admin/add_limited_offer.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def admin_edit_limited_offer_view(request, offer_id):
    offer = get_object_or_404(LimitedOffer, id=offer_id)
    if request.method == 'POST':
        form = LimitedOfferForm(request.POST, instance=offer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Limited offer updated successfully.')
            return redirect('admin_limited_offers')
    else:
        form = LimitedOfferForm(instance=offer)
    return render(request, 'store/admin/add_limited_offer.html', {'form': form, 'offer': offer})

@login_required
@user_passes_test(is_admin)
def admin_toggle_limited_offer_view(request, offer_id):
    offer = get_object_or_404(LimitedOffer, id=offer_id)
    offer.is_active = not offer.is_active
    offer.save(update_fields=['is_active'])
    messages.success(request, f"Offer {'activated' if offer.is_active else 'deactivated'} successfully.")
    return redirect('admin_limited_offers')

@login_required
@user_passes_test(is_admin)
def admin_delete_limited_offer_view(request, offer_id):
    offer = get_object_or_404(LimitedOffer, id=offer_id)
    offer.delete()
    messages.success(request, 'Offer deleted successfully.')
    return redirect('admin_limited_offers')


def about_view(request):
    services = Service.objects.filter(is_active=True)
    contact = ContactInfo.objects.first()
    map_url = None
    if contact:
        # Prefer a proper Google Maps embed URL if provided
        raw = (contact.map_embed_url or '').strip()
        if raw and 'google.com/maps/embed' in raw:
            map_url = raw
        else:
            # Fallback: build a query-based embed from the address
            parts = [
                contact.address_line1 or '',
                contact.address_line2 or '',
                contact.city or '',
                contact.state or '',
                contact.postal_code or '',
                contact.country or '',
            ]
            full_addr = ' '.join([p for p in parts if p]).strip()
            if full_addr:
                map_url = f"https://www.google.com/maps?q={quote_plus(full_addr)}&output=embed"
    return render(request, 'store/about.html', {
        'services': services,
        'contact': contact,
        'map_url': map_url,
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
    # Collect up to 5 images and 2 videos
    images = list(FishMedia.objects.filter(fish=fish, media_type='image')[:5])
    videos = list(FishMedia.objects.filter(fish=fish, media_type='video')[:2])
    media = images + videos
    return render(request, 'store/customer/fish_detail.html', {'fish': fish, 'media': media})


@login_required
@user_passes_test(is_customer)
def customer_accessories_view(request):
    """List available accessories for customers"""
    accessories_qs = Accessory.objects.filter(is_active=True)
    # query params
    q = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()
    sort = request.GET.get('sort', '').strip()

    if q:
        accessories_qs = accessories_qs.filter(
            Q(name__icontains=q) | Q(description__icontains=q) | Q(category__name__icontains=q)
        )

    if category_id:
        try:
            accessories_qs = accessories_qs.filter(category_id=int(category_id))
        except ValueError:
            pass

    # Sorting
    if sort == 'price_asc':
        accessories_qs = accessories_qs.order_by('price')
    elif sort == 'price_desc':
        accessories_qs = accessories_qs.order_by('-price')
    else:
        # default: newest first
        # fallback to created_at if present
        if hasattr(Accessory, 'created_at'):
            accessories_qs = accessories_qs.order_by('-created_at')
        else:
            accessories_qs = accessories_qs.order_by('-id')

    # Pagination
    page_size = 12
    paginator = Paginator(accessories_qs, page_size)
    page = request.GET.get('page', 1)
    try:
        accessories_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        accessories_page = paginator.page(1)

    # If AJAX request, return partial (render the grid with the page)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render(request, 'store/customer/_accessory_grid.html', {'accessories': accessories_page}).content.decode('utf-8')
        return JsonResponse({'html': html})

    categories = Category.objects.all()

    return render(request, 'store/customer/accessories.html', {
        'accessories': accessories_page,
        'search_query': q,
        'categories': categories,
        'selected_category': category_id,
        'current_sort': sort,
    })


@login_required
@user_passes_test(is_customer)
def accessory_detail_view(request, accessory_id):
    accessory = get_object_or_404(Accessory, id=accessory_id, is_active=True)
    return render(request, 'store/customer/accessory_detail.html', {'accessory': accessory})


# Admin: Manage Fish Media
@login_required
@user_passes_test(is_admin)
def admin_fish_media_view(request, fish_id):
    fish = get_object_or_404(Fish, id=fish_id)
    media_items = FishMedia.objects.filter(fish=fish)

    if request.method == 'POST':
        form = FishMediaForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.fish = fish
            # Basic validation: require either file or external_url
            if not obj.file and not obj.external_url:
                messages.error(request, 'Please provide a file or an external URL.')
            else:
                obj.save()
                messages.success(request, 'Media added successfully.')
                return redirect('admin_fish_media', fish_id=fish.id)
    else:
        form = FishMediaForm()

    return render(request, 'store/admin/fish_media.html', {
        'fish': fish,
        'media_items': media_items,
        'form': form,
    })


@login_required
@user_passes_test(is_admin)
def admin_delete_fish_media_view(request, media_id):
    media = get_object_or_404(FishMedia, id=media_id)
    fish_id = media.fish.id
    media.delete()
    messages.success(request, 'Media deleted successfully.')
    return redirect('admin_fish_media', fish_id=fish_id)


@login_required
@user_passes_test(is_admin)
def admin_edit_fish_media_view(request, media_id):
    """Edit an existing FishMedia item (title, order, file, external URL, type)."""
    media = get_object_or_404(FishMedia, id=media_id)
    fish = media.fish

    if request.method == 'POST':
        form = FishMediaForm(request.POST, request.FILES, instance=media)
        if form.is_valid():
            obj = form.save(commit=False)
            # Require either a file or external URL (for videos). Allow images without external_url.
            if not obj.file and not obj.external_url:
                messages.error(request, 'Please provide a file or an external URL.')
            else:
                obj.save()
                messages.success(request, 'Media updated successfully.')
                return redirect('admin_fish_media', fish_id=fish.id)
    else:
        form = FishMediaForm(instance=media)

    return render(request, 'store/admin/edit_fish_media.html', {
        'fish': fish,
        'media': media,
        'form': form,
    })


@login_required
@user_passes_test(is_customer)
def add_to_cart_view(request, fish_id):
    fish = get_object_or_404(Fish, id=fish_id)
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1

    # Check minimum order quantity
    if quantity < fish.minimum_order_quantity:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': f'Minimum order quantity for {fish.name} is {fish.minimum_order_quantity}.'}, status=400)
        messages.error(request, f'Minimum order quantity for {fish.name} is {fish.minimum_order_quantity}.')
        return redirect('fish_detail', fish_id=fish_id)

    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        fish=fish,
        defaults={'quantity': quantity}
    )

    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    # If AJAX, return JSON including combined cart count
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        accessory_items = AccessoryCart.objects.filter(user=request.user)
        cart_items = Cart.objects.filter(user=request.user)
        total_items = (cart_items.aggregate(total=models.Sum('quantity'))['total'] or 0) + (accessory_items.aggregate(total=models.Sum('quantity'))['total'] or 0)
        return JsonResponse({'success': True, 'message': f'{fish.name} added to cart.', 'total_items': int(total_items)})

    messages.success(request, f'{fish.name} added to cart.')
    return redirect('cart')


@login_required
@user_passes_test(is_customer)
@require_POST
def add_accessory_to_cart_view(request, accessory_id):
    from .models import AccessoryCart, Accessory
    accessory = get_object_or_404(Accessory, id=accessory_id)

    # Safely parse quantity
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1

    if quantity < 1:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Invalid quantity.'}, status=400)
        messages.error(request, 'Invalid quantity.')
        return redirect('accessory_detail', accessory_id=accessory_id)

    try:
        cart_item, created = AccessoryCart.objects.get_or_create(
            user=request.user,
            accessory=accessory,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        # AJAX clients expect JSON; regular clients expect redirect
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Return cart summary counts so client can update UI without a full reload
            accessory_items = AccessoryCart.objects.filter(user=request.user)
            total_items = accessory_items.aggregate(total=models.Sum('quantity'))['total'] or 0
            return JsonResponse({'success': True, 'message': f'{accessory.name} added to cart.', 'total_items': int(total_items)})

        messages.success(request, f'{accessory.name} added to cart.')
        return redirect('cart')
    except Exception as e:
        # Log error to console for local debugging and return friendly message
        print(f"Error adding accessory to cart: {e}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Server error adding to cart.'}, status=500)
        messages.error(request, 'Server error adding to cart.')
        return redirect('accessory_detail', accessory_id=accessory_id)


@login_required
@user_passes_test(is_customer)
def cart_view(request):
    cart_items = Cart.objects.filter(user=request.user)
    accessory_items = AccessoryCart.objects.filter(user=request.user)
    total = sum(item.get_total() for item in cart_items) + sum(item.get_total() for item in accessory_items)
    
    return render(request, 'store/customer/cart.html', {
        'cart_items': cart_items,
        'accessory_items': accessory_items,
        'total': total,
    })


@login_required
@user_passes_test(is_customer)
def update_cart_view(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
    quantity = int(request.POST.get('quantity', 1))
    
    # Check minimum order quantity
    if quantity > 0 and quantity < cart_item.fish.minimum_order_quantity:
        messages.error(request, f'Minimum order quantity for {cart_item.fish.name} is {cart_item.fish.minimum_order_quantity}.')
        return redirect('cart')
    
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
def update_accessory_cart_view(request, accessory_cart_id):
    a_item = get_object_or_404(AccessoryCart, id=accessory_cart_id, user=request.user)
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1

    # Check minimum order quantity
    if quantity > 0 and quantity < a_item.accessory.minimum_order_quantity:
        messages.error(request, f'Minimum order quantity for {a_item.accessory.name} is {a_item.accessory.minimum_order_quantity}.')
        return redirect('cart')

    if quantity > 0:
        a_item.quantity = quantity
        a_item.save()
    else:
        a_item.delete()

    return redirect('cart')


@login_required
@user_passes_test(is_customer)
def remove_accessory_cart_view(request, accessory_cart_id):
    a_item = get_object_or_404(AccessoryCart, id=accessory_cart_id, user=request.user)
    a_item.delete()
    messages.success(request, 'Accessory removed from cart.')
    return redirect('cart')


@login_required
@user_passes_test(is_customer)
def checkout_view(request):
    cart_items = Cart.objects.filter(user=request.user)
    accessory_items = AccessoryCart.objects.filter(user=request.user)

    if not cart_items and not accessory_items:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart')

    if request.method == 'POST':
        shipping_address = request.POST.get('shipping_address')
        phone_number = request.POST.get('phone_number')
        payment_method = request.POST.get('payment_method')

        if not shipping_address or not phone_number or not payment_method:
            messages.error(request, 'Please fill in all required fields.')
            total = sum(item.get_total() for item in cart_items) + sum(item.get_total() for item in accessory_items)
            return render(request, 'store/customer/checkout.html', {
                'cart_items': cart_items,
                'accessory_items': accessory_items,
                'total': total,
            })

        # Create order
        total_amount = sum(item.get_total() for item in cart_items) + sum(item.get_total() for item in accessory_items)

        # Apply coupon if exists
        applied_coupon = None
        discount_amount = 0
        final_amount = total_amount

        if 'applied_coupon_code' in request.session:
            try:
                coupon = Coupon.objects.get(code=request.session['applied_coupon_code'])
                if coupon.is_valid() and coupon.can_use(request.user):
                    applied_coupon = coupon
                    discount_amount = (total_amount * coupon.discount_percentage) / 100
                    if coupon.max_discount_amount:
                        discount_amount = min(discount_amount, coupon.max_discount_amount)
                    final_amount = total_amount - discount_amount
                    # Increment coupon usage
                    coupon.times_used += 1
                    coupon.save()
            except Coupon.DoesNotExist:
                pass

        # Generate transaction ID
        transaction_id = f"TXN{uuid.uuid4().hex[:12].upper()}"

        # Set initial payment status based on payment method
        payment_status = 'pending' if payment_method == 'upi' else 'paid'

        order = Order.objects.create(
            user=request.user,
            order_number=Order.generate_order_number(),
            total_amount=total_amount,
            coupon=applied_coupon,
            discount_amount=discount_amount,
            final_amount=final_amount,
            shipping_address=shipping_address,
            phone_number=phone_number,
            payment_method=payment_method,
            payment_status=payment_status,
            transaction_id=transaction_id,
        )

        # Create order items for fishes
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                fish=cart_item.fish,
                quantity=cart_item.quantity,
                price=cart_item.fish.price,
            )
            # Update fish stock
            cart_item.fish.stock_quantity -= cart_item.quantity
            cart_item.fish.save()

        # Create accessory order items
        for a_item in accessory_items:
            OrderAccessoryItem.objects.create(
                order=order,
                accessory=a_item.accessory,
                quantity=a_item.quantity,
                price=a_item.accessory.price,
            )
            # Update accessory stock
            a_item.accessory.stock_quantity -= a_item.quantity
            a_item.accessory.save()

        # Clear carts
        cart_items.delete()
        accessory_items.delete()

        # Clear coupon session
        if 'applied_coupon_code' in request.session:
            del request.session['applied_coupon_code']

        # Redirect to UPI payment page if UPI is selected
        if payment_method == 'upi':
            return redirect('upi_payment', order_id=order.id)

        messages.success(request, f'Order placed successfully! Order number: {order.order_number}')
        return redirect('order_detail', order_id=order.id)

    total = sum(item.get_total() for item in cart_items) + sum(item.get_total() for item in accessory_items)
    
    # Get available coupons for the user
    now = timezone.now()
    available_coupons = Coupon.objects.filter(
        is_active=True,
        show_in_suggestions=True,
        valid_from__lte=now,
        valid_until__gte=now
    ).filter(
        Q(coupon_type='all') |
        Q(coupon_type='favorites', user__is_favorite=True) if request.user.is_favorite else Q(coupon_type='normal')
    ).exclude(
        usage_limit__isnull=False,
        times_used__gte=models.F('usage_limit')
    ).filter(
        Q(min_order_amount__isnull=True) | Q(min_order_amount__lte=total)
    ).order_by('-discount_percentage')[:5]  # Show top 5 best coupons
    
    # Get applied coupon from session
    applied_coupon = None
    discount = 0
    final_total = total
    
    if 'applied_coupon_code' in request.session:
        try:
            coupon = Coupon.objects.get(code=request.session['applied_coupon_code'])
            if coupon.is_valid() and coupon.can_use(request.user):
                applied_coupon = coupon
                discount = (total * coupon.discount_percentage) / 100
                if coupon.max_discount_amount:
                    discount = min(discount, coupon.max_discount_amount)
                final_total = total - discount
        except Coupon.DoesNotExist:
            del request.session['applied_coupon_code']
    
    return render(request, 'store/customer/checkout.html', {
        'cart_items': cart_items,
        'total': total,
        'applied_coupon': applied_coupon,
        'discount': discount,
        'final_total': final_total,
        'available_coupons': available_coupons,
    })


@login_required
@user_passes_test(is_customer)
@require_POST
def apply_coupon_view(request):
    """AJAX view to apply coupon code"""
    try:
        coupon_code = request.POST.get('coupon_code', '').strip().upper()

        if not coupon_code:
            return JsonResponse({'success': False, 'message': 'Please enter a coupon code'})

        try:
            coupon = Coupon.objects.get(code=coupon_code)
        except Coupon.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid coupon code'})

        # Validate coupon
        if not coupon.is_active:
            return JsonResponse({'success': False, 'message': 'This coupon is no longer active'})

        # Check validity with detailed error
        now = timezone.now()
        if coupon.valid_from and now < coupon.valid_from:
            return JsonResponse({
                'success': False,
                'message': f'This coupon is not valid yet. Valid from: {coupon.valid_from.strftime("%d %b %Y, %I:%M %p")}'
            })

        if coupon.valid_until and now > coupon.valid_until:
            return JsonResponse({
                'success': False,
                'message': f'This coupon expired on: {coupon.valid_until.strftime("%d %b %Y, %I:%M %p")}'
            })

        # Check usage limit
        if coupon.usage_limit and coupon.times_used >= coupon.usage_limit:
            return JsonResponse({'success': False, 'message': 'This coupon has reached its usage limit'})

        # Check if user can use this coupon
        if coupon.coupon_type == 'favorites' and not request.user.is_favorite:
            return JsonResponse({'success': False, 'message': 'This coupon is only for favorite customers'})

        if coupon.coupon_type == 'normal' and request.user.is_favorite:
            return JsonResponse({'success': False, 'message': 'This coupon is only for normal users'})

        # Calculate cart total including accessories
        cart_items = Cart.objects.filter(user=request.user)
        accessory_items = AccessoryCart.objects.filter(user=request.user)
        total = sum(item.get_total() for item in cart_items) + sum(item.get_total() for item in accessory_items)

        # Check minimum order amount
        if coupon.min_order_amount and total < coupon.min_order_amount:
            return JsonResponse({
                'success': False,
                'message': f'Minimum order amount of ₹{coupon.min_order_amount} required'
            })

        # Calculate discount
        discount = (total * coupon.discount_percentage) / 100
        if coupon.max_discount_amount:
            discount = min(discount, coupon.max_discount_amount)

        final_total = total - discount

        # Store in session
        request.session['applied_coupon_code'] = coupon_code

        return JsonResponse({
            'success': True,
            'message': f'Coupon applied! You saved ₹{discount:.2f}',
            'discount': float(discount),
            'final_total': float(final_total),
            'coupon_code': coupon_code,
            'discount_percentage': float(coupon.discount_percentage)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


@login_required
@user_passes_test(is_customer)
@require_POST
def remove_coupon_view(request):
    """AJAX view to remove applied coupon"""
    if 'applied_coupon_code' in request.session:
        del request.session['applied_coupon_code']
    
    cart_items = Cart.objects.filter(user=request.user)
    accessory_items = AccessoryCart.objects.filter(user=request.user)
    total = sum(item.get_total() for item in cart_items) + sum(item.get_total() for item in accessory_items)
    
    return JsonResponse({
        'success': True,
        'message': 'Coupon removed',
        'total': float(total)
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
    existing_review = Review.objects.filter(user=request.user, order=order).first()
    review_form = None
    if order.status == 'delivered' and not existing_review:
        review_form = ReviewForm()
    return render(request, 'store/customer/order_detail.html', {
        'order': order,
        'review_form': review_form,
        'existing_review': existing_review,
    })


@login_required
@user_passes_test(is_customer)
def submit_review_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status != 'delivered':
        messages.error(request, 'You can only review a delivered order.')
        return redirect('order_detail', order_id=order.id)
    if Review.objects.filter(user=request.user, order=order).exists():
        messages.info(request, 'You have already reviewed this order.')
        return redirect('order_detail', order_id=order.id)
    form = ReviewForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.order = order
            review.save()
            messages.success(request, 'Review submitted successfully!')
            return redirect('order_detail', order_id=order.id)
        else:
            messages.error(request, 'Please correct the errors in your review form.')
    return redirect('order_detail', order_id=order.id)


@login_required
@user_passes_test(is_customer)
def cancel_order_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if request.method == 'POST':
        # Only allow cancellation for pending or processing orders
        if order.status in ['pending', 'processing']:
            order.status = 'cancelled'
            order.save()
            messages.success(request, f'Order #{order.order_number} has been cancelled successfully.')
        else:
            messages.error(request, f'Order #{order.order_number} cannot be cancelled at this stage.')
        
        return redirect('order_detail', order_id=order.id)
    
    return redirect('order_detail', order_id=order.id)


# UPI Payment Views
@login_required
@user_passes_test(is_customer)
def upi_payment_view(request, order_id):
    """Display UPI payment page with QR code and payment options"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Check if payment is already completed
    if order.payment_status == 'paid':
        messages.info(request, 'This order has already been paid.')
        return redirect('order_detail', order_id=order.id)
    
    # Check if order is cancelled
    if order.status == 'cancelled':
        messages.error(request, 'Cannot process payment for a cancelled order.')
        return redirect('order_detail', order_id=order.id)
    
    # Generate UPI payment string
    # Format: upi://pay?pa=UPI_ID&pn=MERCHANT_NAME&am=AMOUNT&tn=TRANSACTION_NOTE&cu=INR
    upi_id = "muhzinmuhammed4@oksbi"  # Replace with your actual UPI ID
    merchant_name = settings.SITE_NAME
    amount = str(order.total_amount)
    transaction_note = f"Order {order.order_number}"
    
    upi_string = f"upi://pay?pa={upi_id}&pn={merchant_name}&am={amount}&tn={transaction_note}&cu=INR"
    
    # Generate QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(upi_string)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for embedding in HTML
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    # UPI app deep links
    upi_apps = {
        'phonepe': f"phonepe://pay?pa={upi_id}&pn={merchant_name}&am={amount}&tn={transaction_note}&cu=INR",
        'googlepay': f"gpay://upi/pay?pa={upi_id}&pn={merchant_name}&am={amount}&tn={transaction_note}&cu=INR",
        'paytm': f"paytmmp://pay?pa={upi_id}&pn={merchant_name}&am={amount}&tn={transaction_note}&cu=INR",
    }
    
    context = {
        'order': order,
        'upi_id': upi_id,
        'upi_string': upi_string,
        'qr_code': qr_code_base64,
        'upi_apps': upi_apps,
    }
    
    return render(request, 'store/customer/upi_payment.html', context)


@login_required
@user_passes_test(is_customer)
def verify_upi_payment(request, order_id):
    """Verify UPI payment and update order status"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if request.method == 'POST':
        # In a real scenario, you would verify with payment gateway
        # For now, we'll simulate successful payment
        upi_transaction_id = request.POST.get('upi_transaction_id', '').strip()
        
        if upi_transaction_id:
            # Update order with payment details
            order.transaction_id = upi_transaction_id
            order.payment_status = 'paid'
            order.save()
            
            messages.success(request, f'Payment successful! Your order has been confirmed.')
            return redirect('order_detail', order_id=order.id)
        else:
            messages.error(request, 'Please enter a valid UPI transaction ID.')
            return redirect('upi_payment', order_id=order.id)
    
    return redirect('upi_payment', order_id=order.id)


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
    
    if search_query:
        fishes = fishes.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    # If AJAX, return only the rendered table HTML so the client can update it
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('store/staff/_fish_table.html', {'fishes': fishes}, request=request)
        # If there are no fishes, still return the empty-state HTML block so the client can replace container
        if not fishes:
            empty_html = render_to_string('store/staff/fish_list.html', {'fishes': fishes, 'search_query': search_query}, request=request)
            return JsonResponse({'html': html + empty_html})
        return JsonResponse({'html': html})

    return render(request, 'store/staff/fish_list.html', {
        'fishes': fishes,
        'search_query': search_query,
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


# Staff: Manage Fish Media
@login_required
@user_passes_test(is_staff)
def staff_fish_media_view(request, fish_id):
    fish = get_object_or_404(Fish, id=fish_id)
    media_items = FishMedia.objects.filter(fish=fish)

    if request.method == 'POST':
        form = FishMediaForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.fish = fish
            # Require either file or external URL
            if not obj.file and not obj.external_url:
                messages.error(request, 'Please provide a file or an external URL.')
            else:
                obj.save()
                messages.success(request, 'Media added successfully.')
                return redirect('staff_fish_media', fish_id=fish.id)
    else:
        form = FishMediaForm()

    return render(request, 'store/staff/fish_media.html', {
        'fish': fish,
        'media_items': media_items,
        'form': form,
    })


@login_required
@user_passes_test(is_staff)
def staff_delete_fish_media_view(request, media_id):
    media = get_object_or_404(FishMedia, id=media_id)
    fish_id = media.fish.id
    media.delete()
    messages.success(request, 'Media deleted successfully.')
    return redirect('staff_fish_media', fish_id=fish_id)


@login_required
@user_passes_test(is_staff)
def staff_edit_fish_media_view(request, media_id):
    media = get_object_or_404(FishMedia, id=media_id)
    fish = media.fish

    if request.method == 'POST':
        form = FishMediaForm(request.POST, request.FILES, instance=media)
        if form.is_valid():
            obj = form.save(commit=False)
            if not obj.file and not obj.external_url:
                messages.error(request, 'Please provide a file or an external URL.')
            else:
                obj.save()
                messages.success(request, 'Media updated successfully.')
                return redirect('staff_fish_media', fish_id=fish.id)
    else:
        form = FishMediaForm(instance=media)

    return render(request, 'store/staff/edit_fish_media.html', {
        'fish': fish,
        'media': media,
        'form': form,
    })


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
    sorted_months = sorted(month_data.keys())  # Oldest first for proper chart display
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
        # Staff creation with admin-provided password (password fields are on the form)
        form = StaffCreateForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'staff'
            user.email_verified = True
            user.is_active = True
            # Set the password provided by the admin
            password = form.cleaned_data.get('password1')
            if password:
                user.set_password(password)
            else:
                user.set_unusable_password()
            user.save()
            # Send a simple welcome email (do not include passwords in email)
            try:
                send_mail(
                    f'You have been added as Staff - {settings.SITE_NAME}',
                    (
                        f"Hello {user.username},\n\n"
                        f"You've been added as staff to {settings.SITE_NAME}.\n\n"
                        "You can now login using your account credentials. If you did not set a password, please use the password reset flow.\n\n"
                        f"Thanks,\n{settings.SITE_NAME}"
                    ),
                    settings.DEFAULT_FROM_EMAIL or 'noreply@aquafishstore.com',
                    [user.email],
                    fail_silently=False,
                )
                messages.success(request, 'Staff member added and notification email sent successfully.')
            except Exception as e:
                messages.warning(request, f'Staff member added, but failed to send email: {e}')
            return redirect('admin_staff_list')
    else:
        form = StaffCreateForm()
    
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


# -------------------- Services (Admin Managed) --------------------
@login_required
@user_passes_test(is_admin)
def admin_services_view(request):
    services = Service.objects.all()
    return render(request, 'store/admin/services.html', {'services': services})


@login_required
@user_passes_test(is_admin)
def admin_add_service_view(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Service added successfully.')
            return redirect('admin_services')
    else:
        form = ServiceForm()
    return render(request, 'store/admin/add_service.html', {'form': form})


@login_required
@user_passes_test(is_staff)
def staff_accessories_view(request):
    from .models import Accessory
    accessories = Accessory.objects.all()
    return render(request, 'store/staff/accessories.html', {'accessories': accessories})


@login_required
@user_passes_test(is_staff)
def add_accessory_view(request):
    from .models import Accessory
    from .forms import AccessoryForm

    if request.method == 'POST':
        form = AccessoryForm(request.POST, request.FILES)
        if form.is_valid():
            accessory = form.save(commit=False)
            accessory.created_by = request.user
            accessory.save()
            messages.success(request, 'Accessory added successfully.')
            return redirect('staff_accessories')
    else:
        form = AccessoryForm()
    return render(request, 'store/staff/add_accessory.html', {'form': form})


@login_required
@user_passes_test(is_staff)
def accessories_add_view(request):
    """Unified add-accessory page available to staff and admin (uses staff template)."""
    from .forms import AccessoryForm

    if request.method == 'POST':
        form = AccessoryForm(request.POST, request.FILES)
        if form.is_valid():
            accessory = form.save(commit=False)
            accessory.created_by = request.user
            accessory.save()
            messages.success(request, 'Accessory added successfully.')
            # Role-aware redirect
            if hasattr(request.user, 'role') and request.user.role == 'admin':
                return redirect('admin_accessories')
            return redirect('staff_accessories')
    else:
        form = AccessoryForm()

    # Reuse staff add template for simplicity
    return render(request, 'store/staff/add_accessory.html', {'form': form})


@login_required
@user_passes_test(is_staff)
def edit_accessory_view(request, accessory_id):
    from .models import Accessory
    from .forms import AccessoryForm
    accessory = get_object_or_404(Accessory, id=accessory_id)
    if request.method == 'POST':
        form = AccessoryForm(request.POST, request.FILES, instance=accessory)
        if form.is_valid():
            form.save()
            messages.success(request, 'Accessory updated successfully.')
            return redirect('staff_accessories')
    else:
        form = AccessoryForm(instance=accessory)
    return render(request, 'store/staff/edit_accessory.html', {'form': form, 'accessory': accessory})


@login_required
@user_passes_test(is_staff)
@require_POST
def delete_accessory_view(request, accessory_id):
    from .models import Accessory
    accessory = get_object_or_404(Accessory, id=accessory_id)
    accessory.delete()
    messages.success(request, 'Accessory deleted successfully.')
    return redirect('staff_accessories')


@login_required
@user_passes_test(is_admin)
def admin_accessories_view(request):
    from .models import Accessory
    accessories = Accessory.objects.all()
    return render(request, 'store/admin/accessories.html', {'accessories': accessories})


@login_required
@user_passes_test(is_admin)
def admin_add_accessory_view(request):
    from .forms import AccessoryForm
    if request.method == 'POST':
        form = AccessoryForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
            messages.success(request, 'Accessory created successfully.')
            return redirect('admin_accessories')
    else:
        form = AccessoryForm()
    return render(request, 'store/admin/add_accessory.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def admin_edit_accessory_view(request, accessory_id):
    from .models import Accessory
    from .forms import AccessoryForm
    accessory = get_object_or_404(Accessory, id=accessory_id)
    if request.method == 'POST':
        form = AccessoryForm(request.POST, request.FILES, instance=accessory)
        if form.is_valid():
            form.save()
            messages.success(request, 'Accessory updated successfully.')
            return redirect('admin_accessories')
    else:
        form = AccessoryForm(instance=accessory)
    return render(request, 'store/admin/add_accessory.html', {'form': form, 'accessory': accessory})


@login_required
@user_passes_test(is_admin)
@require_POST
def admin_delete_accessory_view(request, accessory_id):
    from .models import Accessory
    accessory = get_object_or_404(Accessory, id=accessory_id)
    accessory.delete()
    messages.success(request, 'Accessory deleted successfully.')
    return redirect('admin_accessories')


@login_required
@user_passes_test(is_admin)
def admin_edit_service_view(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, 'Service updated successfully.')
            return redirect('admin_services')
    else:
        form = ServiceForm(instance=service)
    return render(request, 'store/admin/add_service.html', {'form': form, 'is_edit': True})


@login_required
@user_passes_test(is_admin)
def admin_delete_service_view(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    service.delete()
    messages.success(request, 'Service deleted successfully.')
    return redirect('admin_services')


# -------------------- Contact Info (Admin Managed) --------------------
@login_required
@user_passes_test(is_admin)
@login_required
@user_passes_test(is_admin)
def admin_contact_view(request):
    contact = ContactInfo.objects.first()
    return render(request, 'store/admin/contact.html', {'contact': contact})


@login_required
@user_passes_test(is_admin)
def admin_add_contact_view(request):
    existing = ContactInfo.objects.first()
    if existing:
        return redirect('admin_edit_contact', contact_id=existing.id)
    if request.method == 'POST':
        form = ContactInfoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contact information saved.')
            return redirect('admin_contact')
    else:
        form = ContactInfoForm()
    return render(request, 'store/admin/add_contact.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def admin_edit_contact_view(request, contact_id):
    contact = get_object_or_404(ContactInfo, id=contact_id)
    if request.method == 'POST':
        form = ContactInfoForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contact information updated.')
            return redirect('admin_contact')
    else:
        form = ContactInfoForm(instance=contact)
    return render(request, 'store/admin/add_contact.html', {'form': form, 'is_edit': True})


@login_required
@user_passes_test(is_admin)
def admin_reviews_view(request):
    pending_reviews = Review.objects.filter(approved=False).select_related('user', 'order').order_by('-created_at')
    approved_reviews = Review.objects.filter(approved=True).select_related('user', 'order').order_by('-created_at')
    
    return render(request, 'store/admin/reviews.html', {
        'pending_reviews': pending_reviews,
        'approved_reviews': approved_reviews,
    })


@login_required
@user_passes_test(is_admin)
def admin_approve_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    review.approved = True
    review.save()
    messages.success(request, 'Review approved successfully.')
    return redirect('admin_reviews')


@login_required
@user_passes_test(is_admin)
def admin_reject_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    review.delete()
    messages.success(request, 'Review rejected and deleted.')
    return redirect('admin_reviews')


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


# AJAX endpoint for admin orders filter/search
@login_required
@user_passes_test(is_admin)
@require_GET
def admin_orders_ajax_view(request):
    orders = Order.objects.all().order_by('-created_at')
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
    search = request.GET.get('search', '').strip()
    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(user__username__icontains=search)
        )
    html = render_to_string('store/admin/_orders_table.html', {'orders': orders}, request=request)
    return JsonResponse({'html': html})


@login_required
@user_passes_test(is_admin)
def admin_order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status and new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f'Order status updated to {order.get_status_display()}.')
            return redirect('admin_order_detail', order_id=order.id)
    
    return render(request, 'store/admin/order_detail.html', {'order': order})


@login_required
@user_passes_test(is_admin)
def admin_users_view(request):
    users = CustomUser.objects.filter(role='customer').order_by('-is_favorite', '-created_at')
    return render(request, 'store/admin/users.html', {'users': users})


@login_required
@user_passes_test(is_admin)
def toggle_favorite_user_view(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id, role='customer')
    user.is_favorite = not user.is_favorite
    user.save()
    status = 'added to' if user.is_favorite else 'removed from'
    messages.success(request, f'User {user.username} has been {status} favorites.')
    return redirect('admin_users')


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
    
    # Sheet 1: Orders Summary
    ws1 = wb.active
    ws1.title = "Orders Summary"
    
    # Orders Summary Headers
    summary_headers = [
        'Order Number', 'Customer Username', 'Customer Email', 'Customer Phone', 
        'Total Amount', 'Order Status', 'Payment Method', 'Payment Status', 'Transaction ID',
        'Shipping Address', 'Contact Phone', 'Total Items', 'Order Created', 'Last Updated'
    ]
    ws1.append(summary_headers)
    
    # Style header
    header_fill = PatternFill(start_color="0066CC", end_color="0066CC", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    
    for cell in ws1[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # Orders Summary Data
    for order in orders:
        total_items = order.items.aggregate(total=models.Sum('quantity'))['total'] or 0
        ws1.append([
            order.order_number,
            order.user.username,
            order.user.email,
            order.user.phone_number if order.user.phone_number else 'N/A',
            float(order.total_amount),
            order.get_status_display(),
            order.get_payment_method_display(),
            order.get_payment_status_display(),
            order.transaction_id if order.transaction_id else 'N/A',
            order.shipping_address,
            order.phone_number,
            total_items,
            order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            order.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])
    
    # Auto-adjust column widths for summary sheet
    for column in ws1.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws1.column_dimensions[column_letter].width = adjusted_width
    
    # Sheet 2: Detailed Order Items
    ws2 = wb.create_sheet(title="Order Items Detail")
    
    # Order Items Headers
    items_headers = [
        'Order Number', 'Customer Name', 'Fish Name', 'Fish Breed', 'Fish Category',
        'Quantity', 'Unit Price', 'Item Total', 'Order Status', 'Order Date'
    ]
    ws2.append(items_headers)
    
    # Style items header
    for cell in ws2[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # Order Items Data
    for order in orders:
        for item in order.items.all():
            ws2.append([
                order.order_number,
                order.user.username,
                item.fish.name,
                item.fish.breed.name,
                item.fish.category.name,
                item.quantity,
                float(item.price),
                float(item.get_total()),
                order.get_status_display(),
                order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            ])
    
    # Auto-adjust column widths for items sheet
    for column in ws2.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws2.column_dimensions[column_letter].width = adjusted_width
    
    # Sheet 3: Customer Information
    ws3 = wb.create_sheet(title="Customer Details")
    
    # Get unique customers from filtered orders
    customer_ids = orders.values_list('user_id', flat=True).distinct()
    customers = CustomUser.objects.filter(id__in=customer_ids)
    
    # Customer Headers
    customer_headers = [
        'Username', 'Email', 'Phone Number', 'Date Joined', 
        'Email Verified', 'Total Orders', 'Total Spent'
    ]
    ws3.append(customer_headers)
    
    # Style customer header
    for cell in ws3[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # Customer Data
    for customer in customers:
        customer_orders = orders.filter(user=customer)
        total_orders = customer_orders.count()
        total_spent = customer_orders.aggregate(total=models.Sum('total_amount'))['total'] or 0
        
        ws3.append([
            customer.username,
            customer.email,
            customer.phone_number if customer.phone_number else 'N/A',
            customer.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'Yes' if customer.email_verified else 'No',
            total_orders,
            float(total_spent),
        ])
    
    # Auto-adjust column widths for customer sheet
    for column in ws3.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws3.column_dimensions[column_letter].width = adjusted_width
    
    # Response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="orders_detailed_report.xlsx"'
    wb.save(response)
    return response


# Coupon Management Views
@login_required
@user_passes_test(is_admin)
def admin_coupons_view(request):
    filter_type = request.GET.get('filter', 'all_coupons')
    
    if filter_type == 'all_users':
        coupons = Coupon.objects.filter(coupon_type='all').order_by('-created_at')
    elif filter_type == 'favorites':
        coupons = Coupon.objects.filter(coupon_type='favorites').order_by('-created_at')
    elif filter_type == 'normal':
        coupons = Coupon.objects.filter(coupon_type='normal').order_by('-created_at')
    elif filter_type == 'active':
        coupons = Coupon.objects.filter(is_active=True).order_by('-created_at')
    elif filter_type == 'inactive':
        coupons = Coupon.objects.filter(is_active=False).order_by('-created_at')
    else:
        coupons = Coupon.objects.all().order_by('-created_at')
    
    # Get counts for badges
    all_users_count = Coupon.objects.filter(coupon_type='all').count()
    favorites_count = Coupon.objects.filter(coupon_type='favorites').count()
    normal_count = Coupon.objects.filter(coupon_type='normal').count()
    active_count = Coupon.objects.filter(is_active=True).count()
    inactive_count = Coupon.objects.filter(is_active=False).count()
    
    context = {
        'coupons': coupons,
        'filter_type': filter_type,
        'all_users_count': all_users_count,
        'favorites_count': favorites_count,
        'normal_count': normal_count,
        'active_count': active_count,
        'inactive_count': inactive_count,
    }
    return render(request, 'store/admin/coupons.html', context)


@login_required
@user_passes_test(is_admin)
def admin_add_coupon_view(request):
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            coupon = form.save(commit=False)
            coupon.created_by = request.user
            coupon.save()
            messages.success(request, f'Coupon "{coupon.code}" created successfully!')
            return redirect('admin_coupons')
    else:
        form = CouponForm()
    return render(request, 'store/admin/add_coupon.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def admin_edit_coupon_view(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            form.save()
            messages.success(request, f'Coupon "{coupon.code}" updated successfully!')
            return redirect('admin_coupons')
    else:
        form = CouponForm(instance=coupon)
    return render(request, 'store/admin/add_coupon.html', {'form': form, 'is_edit': True, 'coupon': coupon})


@login_required
@user_passes_test(is_admin)
def admin_delete_coupon_view(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    code = coupon.code
    coupon.delete()
    messages.success(request, f'Coupon "{code}" deleted successfully!')
    return redirect('admin_coupons')


@login_required
@user_passes_test(is_admin)
def admin_toggle_coupon_view(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.is_active = not coupon.is_active
    coupon.save()
    status = 'activated' if coupon.is_active else 'deactivated'
    messages.success(request, f'Coupon "{coupon.code}" has been {status}!')
    return redirect('admin_coupons')


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


@login_required
def change_password_view(request):
    # Only allow users who have verified email to change password
    if not request.user.email_verified:
        messages.error(request, 'Please verify your email before changing password.')
        return redirect('profile')

    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Keep user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed successfully.')
            return redirect('profile')
    else:
        form = ChangePasswordForm(request.user)

    return render(request, 'store/change_password.html', {'form': form})

