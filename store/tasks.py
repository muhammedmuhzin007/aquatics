from __future__ import annotations
from celery import shared_task
from django.conf import settings
import logging

from .models import Order
from .views import _send_order_email


class _DummyRequest:
    """Small helper to provide build_absolute_uri for background tasks.

    If `site_base` is provided it will be used as the absolute base URL.
    """
    def __init__(self, site_base: str | None):
        self.site_base = (site_base or '').rstrip('/')

    def build_absolute_uri(self, path: str) -> str:
        if not self.site_base:
            return path
        if path.startswith('/'):
            return f"{self.site_base}{path}"
        return f"{self.site_base}/{path}"


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 5})
def send_order_email(self, order_id: int, template_base: str, subject: str, recipient_email: str, site_base: str | None = None):
    """Background task to send order-related emails (invoice/cancellation).

    Uses the existing `_send_order_email` helper so behavior is consistent.
    """
    logger = logging.getLogger(__name__)
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        logger.warning('Order %s not found for send_order_email task', order_id)
        return

    req = _DummyRequest(site_base)
    try:
        _send_order_email(order, template_base, subject, recipient_email, request=req)
        logger.info('send_order_email task completed for order %s', order.order_number)
    except Exception as exc:
        logger.exception('send_order_email task failed for order %s', order_id)
        # Let Celery retry according to autoretry_for / retry_backoff
        raise
