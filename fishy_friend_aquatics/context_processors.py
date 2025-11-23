from django.conf import settings

def site_settings(request):
    return {
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'Fishy Friend Aquatics'),
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

    return {
        'has_active_accessories': has_active,
    }
