from .mock import MockProvider
from .stripe import StripeProvider
import os

# In the future, add: from .stripe import StripeProvider, etc.

PROVIDERS = {
    'mock': MockProvider,
    'stripe': StripeProvider,
}

def get_payment_provider(name=None):
    from django.conf import settings
    if not name:
        # Prefer environment override, then Django settings, then default to 'stripe'.
        name = os.environ.get('PAYMENT_PROVIDER') or getattr(settings, 'PAYMENT_PROVIDER', 'stripe')
    name = name.lower()
    provider_cls = PROVIDERS.get(name)
    if not provider_cls:
        raise Exception(f'Unknown payment provider: {name}')
    return provider_cls()
