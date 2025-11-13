from django import template
from django.db.models import Sum

register = template.Library()


@register.simple_tag(takes_context=True)
def cart_count(context):
    """Return total quantity of items in both Cart and AccessoryCart for the current user."""
    request = context.get('request')
    if not request:
        return 0
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return 0

    from ..models import Cart, AccessoryCart

    cart_total = Cart.objects.filter(user=user).aggregate(total=Sum('quantity'))['total'] or 0
    acc_total = AccessoryCart.objects.filter(user=user).aggregate(total=Sum('quantity'))['total'] or 0

    try:
        return int(cart_total) + int(acc_total)
    except Exception:
        return 0
