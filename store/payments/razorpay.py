"""Provider stub removed.

This file used to contain a provider implementation and is retained
only as a placeholder to avoid accidental import errors. The project
uses the Stripe and mock providers located under `store.payments`.
"""

def stub(*args, **kwargs):
    raise Exception('Provider removed; use the stripe or mock provider')


class RemovedProvider:
    __init__ = stub
    create_order = stub
    verify_payment = stub
    handle_webhook = stub
