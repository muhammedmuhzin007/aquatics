from django import template

register = template.Library()

@register.filter(name='rupees')
def rupees(value, decimals=2):
    """Format a number/Decimal as Indian Rupees with configurable decimal places."""
    try:
        if value is None:
            value = 0
        amount = float(value)
        decimals = int(decimals)
        if decimals < 0:
            decimals = 0
        formatted = format(amount, f",.{decimals}f")
        return f"₹{formatted}"
    except (ValueError, TypeError):
        return value
