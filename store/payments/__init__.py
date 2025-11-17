from .razorpay import RazorpayProvider
from .mock import MockProvider

# In the future, add: from .stripe import StripeProvider, etc.

PROVIDERS = {
    'razorpay': RazorpayProvider,
    'mock': MockProvider,
    # 'stripe': StripeProvider, # Example for future
}

def get_payment_provider(name=None):
    from django.conf import settings
    if not name:
        name = getattr(settings, 'PAYMENT_PROVIDER', 'razorpay')
    name = name.lower()
    provider_cls = PROVIDERS.get(name)
    if not provider_cls:
        raise Exception(f'Unknown payment provider: {name}')
    return provider_cls()
