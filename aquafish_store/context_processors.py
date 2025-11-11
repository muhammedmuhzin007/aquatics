from django.conf import settings

def site_settings(request):
    """Expose selected settings (like SITE_NAME) to all templates."""
    return {
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'Fishy Friend Aquatics'),
    }
