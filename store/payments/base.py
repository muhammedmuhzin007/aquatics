from abc import ABC, abstractmethod

class BasePaymentProvider(ABC):
    """
    Abstract base class for payment providers.
    """
    @abstractmethod
    def create_order(self, order):
        """Create a provider order and return provider order id and client data."""
        pass

    @abstractmethod
    def verify_payment(self, data):
        """Verify payment signature and return True/False."""
        pass

    @abstractmethod
    def handle_webhook(self, request):
        """Process webhook and return status/result."""
        pass
