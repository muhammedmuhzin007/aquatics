from django import template
from django.db.models import Sum

register = template.Library()


@register.simple_tag(takes_context=True)
def cart_count(context):
    """Return total quantity of fish, accessory, and plant items for the current user."""
    request = context.get('request')
    if not request:
        return 0
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        cart = request.session.get('guest_cart') or {}
        total = 0
        for section in ('fish', 'accessories', 'plants'):
            entries = cart.get(section) if isinstance(cart, dict) else None
            if not isinstance(entries, dict):
                continue
            for data in entries.values():
                try:
                    total += int(data.get('quantity', 0) or 0)
                except Exception:
                    continue
        return total

    from ..models import Cart, AccessoryCart, PlantCart

    cart_total = Cart.objects.filter(user=user).aggregate(total=Sum('quantity'))['total'] or 0
    acc_total = AccessoryCart.objects.filter(user=user).aggregate(total=Sum('quantity'))['total'] or 0
    plant_total = PlantCart.objects.filter(user=user).aggregate(total=Sum('quantity'))['total'] or 0

    try:
        return int(cart_total) + int(acc_total) + int(plant_total)
    except Exception:
        return 0
