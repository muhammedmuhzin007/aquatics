from django.conf import settings

def site_settings(request):
    return {
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'FISHY FRIEND AQUA'),
    }


def global_flags(request):
    """Provide small site-wide boolean flags for templates.

    - has_active_accessories: True when at least one accessory is active.
    """
    try:
        from store.models import Accessory
        has_active = Accessory.objects.filter(is_active=True).exists()
    except Exception:
        has_active = False
    # Check for active combos as well so templates can conditionally show a Combos nav
    try:
        from store.models import ComboOffer
        # Only consider combos visible to customers: active and all items available with sufficient stock
        combos_qs = ComboOffer.objects.filter(is_active=True).prefetch_related('items__fish')
        has_active_combos = False
        for combo in combos_qs:
            ok = True
            for item in combo.items.all():
                fish = item.fish
                req_qty = int(item.quantity or 1)
                if not getattr(fish, 'is_available', True) or getattr(fish, 'stock_quantity', 0) < req_qty:
                    ok = False
                    break
            if ok:
                has_active_combos = True
                break
    except Exception:
        has_active_combos = False

    # Attach unread notification counts for staff/admin users
    unread_count = 0
    recent_notifications = []
    # Show blog nav only when at least one published post exists
    has_published_blogs = False
    try:
        user = getattr(request, 'user', None)
        if user and user.is_authenticated and getattr(user, 'role', None) in ('staff', 'admin'):
            from store.models import Notification
            # only surface unread notifications in the dropdown/context so that
            # marked notifications do not reappear after a refresh
            unread_count = Notification.objects.filter(is_read=False).count()
            recent_notifications = list(Notification.objects.filter(is_read=False).order_by('-created_at')[:5])
    except Exception:
        unread_count = 0
        recent_notifications = []

    try:
        from store.models import BlogPost
        has_published_blogs = BlogPost.objects.filter(is_published=True).exists()
    except Exception:
        has_published_blogs = False

    return {
        'has_active_accessories': has_active,
        'has_active_combos': has_active_combos,
        'has_published_blogs': has_published_blogs,
        'unread_notifications_count': unread_count,
        'recent_notifications': recent_notifications,
    }
