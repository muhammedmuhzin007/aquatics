"""Lightweight mock payment provider for local testing.

Provides simple create_order and verify_payment methods that do not
call external services. Useful for CI / local smoke tests.
"""
from decimal import Decimal

class MockProvider:
    def create_order(self, order):
        # Return a payload similar to Razorpay's expected response
        amount_paise = int(float(order.final_amount or 0) * 100)
        return {
            'razorpay_order_id': f'mock_order_{order.id}',
            'razorpay_key': 'rzp_test_mock_key',
            'amount': amount_paise,
            'currency': 'INR',
        }

    def verify_payment(self, data):
        # Accept anything in tests
        return True

    def handle_webhook(self, request):
        return True, {}
