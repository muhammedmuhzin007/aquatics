from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.conf import settings
import json
import logging

from .models import Order
from .payments import get_payment_provider

logger = logging.getLogger(__name__)


def _finalize_payment(provider_order, payment_id=None, request=None):
    """Locate the Order by provider_order id (or fallback) and mark it paid, set tx id and send invoice.

    Returns True if an Order was found and processed, False otherwise.
    """
    order = None
    try:
        if provider_order:
            order = Order.objects.filter(provider_order_id=provider_order).first()
        if not order:
            order = Order.objects.filter(order_number__iexact=provider_order).first()
    except Exception:
        logger.exception('Error locating Order for provider_order %s', provider_order)
        return False

    if not order:
        logger.warning('No Order matched provider_order %s', provider_order)
        return False

    try:
        if payment_id:
            order.transaction_id = payment_id
        order.payment_status = 'paid'
        if order.status == 'pending':
            order.status = 'processing'
        order.save()

        # Send invoice using Celery task if available, otherwise synchronous fallback
        try:
            from store.tasks import send_order_email
            site_base = request.build_absolute_uri('/') if request is not None else getattr(settings, 'SITE_URL', None)
            send_order_email.delay(order.id, 'invoice', f'Invoice - {settings.SITE_NAME} - {order.order_number}', order.user.email, site_base)
        except Exception:
            logger.info('Celery unavailable or task failed; sending invoice synchronously for %s', order.order_number)
            try:
                from store.views import _send_order_email
                _send_order_email(order, 'invoice', f'Invoice - {settings.SITE_NAME} - {order.order_number}', order.user.email, request=request)
            except Exception:
                logger.exception('Synchronous invoice send failed for order %s', order.order_number)
        return True
    except Exception:
        logger.exception('Failed to finalize payment for order %s (provider_order=%s)', getattr(order, 'order_number', 'N/A'), provider_order)
        return False


def create_razorpay_payment(request, order_id):
    """Create a razorpay order for the given order id and return payload for client."""
    if request.method != 'POST' and request.method != 'GET':
        return HttpResponseBadRequest('Only POST/GET allowed')

    order = get_object_or_404(Order, id=order_id)
    provider = get_payment_provider('razorpay')
    try:
        payload = provider.create_order(order)
        # Persist provider order id on our Order so we can map callbacks/verify
        try:
            prov_id = payload.get('razorpay_order_id') or payload.get('provider_order_id')
            if prov_id:
                order.provider_order_id = prov_id
                order.save()
        except Exception:
            # Don't fail the create flow when saving provider id; log and continue
            import logging
            logging.getLogger(__name__).exception('Failed to persist provider_order_id for order %s', order.order_number)
        return JsonResponse(payload)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=502)


@csrf_exempt
def verify_razorpay_payment(request):
    """Verify razorpay payment (expects JSON payload with payment_id/order_id/signature)."""
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return HttpResponseBadRequest('Invalid JSON')

    provider = get_payment_provider('razorpay')
    ok = provider.verify_payment(data)
    if not ok:
        return JsonResponse({'success': False})

    payment_id = data.get('razorpay_payment_id')
    provider_order = data.get('razorpay_order_id')

    processed = _finalize_payment(provider_order, payment_id=payment_id, request=request)

    return JsonResponse({'success': bool(processed)})


@csrf_exempt
def razorpay_webhook(request):
    """Receive Razorpay webhooks and hand off to provider for verification."""
    provider = get_payment_provider('razorpay')
    ok, event_or_msg = provider.handle_webhook(request)
    if not ok:
        return HttpResponse(status=400)

    # event_or_msg should be the event dict when ok
    try:
        event = event_or_msg if isinstance(event_or_msg, dict) else {}
        event_name = event.get('event') or ''
        # Handle payment captured events: mark order paid and send invoice
        if event_name == 'payment.captured':
            payload = event.get('payload', {})
            payment_entity = payload.get('payment', {}).get('entity', {})
            provider_order = payment_entity.get('order_id')
            payment_id = payment_entity.get('id')
            if provider_order:
                _finalize_payment(provider_order, payment_id=payment_id, request=request)

        # Optionally: handle order.paid or other events in future
    except Exception:
        logger.exception('Error processing webhook event')

    return HttpResponse(status=200)
