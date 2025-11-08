from django import template

register = template.Library()

@register.filter(name='rupees')
def rupees(value):
    """Format a number/Decimal as Indian Rupees with symbol and two decimals.
    Examples: 1234.5 -> ₹1,234.50
    """
    try:
        if value is None:
            return "₹0.00"
        # Ensure it's a float/decimal and format with thousand separators
        amount = float(value)
        return f"₹{amount:,.2f}"
    except (ValueError, TypeError):
        return value
