"""Lightweight mock payment provider for local testing.

Provides simple create_order and verify_payment methods that do not
call external services. Useful for CI / local smoke tests.
"""
from decimal import Decimal

class MockProvider:
    def create_order(self, order):
        # Return a simple provider-agnostic payload for tests
        amount_paise = int(float(order.final_amount or 0) * 100)
        return {
            'provider_order_id': f'mock_order_{order.id}',
            'provider_key': 'mock_test_key',
            'amount': amount_paise,
            'currency': 'INR',
            # also include common alternative keys for broader compatibility
            'id': f'mock_order_{order.id}',
            'payment_intent_id': f'mock_pi_{order.id}',
        }

    def verify_payment(self, data):
        # Accept anything in tests
        return True

    def handle_webhook(self, request):
        return True, {}
