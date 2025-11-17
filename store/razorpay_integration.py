import hmac
import hashlib
import json
import logging
from django.conf import settings
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

logger = logging.getLogger(__name__)


@login_required
@require_POST
@csrf_protect
def create_razorpay_order(request, order_id):
    """Create a Razorpay order for the given Order and return client data (modularized)."""
    try:
        from .models import Order
        from store.payments import get_payment_provider
    except Exception:
        return HttpResponseBadRequest('Order model unavailable')

    order = get_object_or_404(Order, id=order_id, user=request.user)

    try:
        # Respect configured provider (allows using a mock provider in tests)
        provider_name = getattr(settings, 'PAYMENT_PROVIDER', 'razorpay')
        provider = get_payment_provider(provider_name)
        data = provider.create_order(order)
    except Exception as exc:
        logger.exception('Failed to create provider order for order %s: %s', order.order_number, exc)
        return HttpResponse('Failed to create provider order', status=502)

    # Store provider order id in the dedicated field so webhook can find it
    try:
        order.provider_order_id = data.get('razorpay_order_id')
        order.save(update_fields=['provider_order_id'])
    except Exception:
        logger.exception('Failed to save provider order id to order.provider_order_id for %s', order.order_number)

    return JsonResponse(data)


@csrf_exempt
def razorpay_webhook(request):
    """Handle Razorpay webhooks. Verifies signature and marks orders paid.

    Expects the `X-Razorpay-Signature` header containing HMAC SHA256 of the
    request body using your `RAZORPAY_WEBHOOK_SECRET`.
    """
    payload = request.body or b''
    signature = request.META.get('HTTP_X_RAZORPAY_SIGNATURE')
    secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '')

    if not signature or not secret:
        logger.warning('Missing signature or webhook secret')
        return HttpResponseBadRequest('Missing signature or secret')

    computed = hmac.new(secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed, signature):
        logger.warning('Invalid razorpay webhook signature')
        return HttpResponseBadRequest('Invalid signature')

    try:
        event = json.loads(payload.decode('utf-8'))
    except Exception:
        return HttpResponseBadRequest('Invalid JSON')

    # Only handle payment.captured for now
    ev = event.get('event')
    if ev == 'payment.captured':
        try:
            payment = event['payload']['payment']['entity']
            razor_order_id = payment.get('order_id')
            payment_id = payment.get('id')
            amount = payment.get('amount') / 100.0 if payment.get('amount') else None

            # Find order by the stored provider order id (we stored it in provider_order_id)
            from .models import Order
            try:
                order = Order.objects.get(provider_order_id=razor_order_id)
            except Order.DoesNotExist:
                logger.warning('Order for razor_order_id %s not found', razor_order_id)
                return HttpResponse('Order not found', status=404)

            # Idempotent: only mark paid if not already paid
            if order.payment_status != 'paid':
                if amount is None or abs(float(order.final_amount) - float(amount)) < 0.01:
                    order.payment_status = 'paid'
                    order.transaction_id = payment_id
                    order.save(update_fields=['payment_status', 'transaction_id'])
                    # enqueue invoice send
                    try:
                        from store.tasks import send_order_email
                        send_order_email.delay(order.id, 'invoice', f'Invoice - {settings.SITE_NAME} - {order.order_number}', order.user.email, settings.SITE_URL)
                    except Exception:
                        logger.exception('Failed to enqueue send_order_email task for order %s', order.order_number)
                        # fallback to synchronous send
                        try:
                            from .views import _send_order_email
                            _send_order_email(order, 'invoice', f'Invoice - {settings.SITE_NAME} - {order.order_number}', order.user.email, request=None)
                        except Exception:
                            logger.exception('Synchronous invoice send failed for order %s', order.order_number)
                else:
                    logger.warning('Payment amount mismatch for order %s: expected %s got %s', order.order_number, order.final_amount, amount)
        except Exception:
            logger.exception('Error processing payment.captured webhook')
            return HttpResponse('Error', status=500)

    # Respond 200 for other events too to acknowledge receipt
    return HttpResponse('OK')


@csrf_exempt
def verify_razorpay_payment(request):
    """Verify payment returned by Razorpay Checkout (client-side handler).

    Expected JSON body: {
      razorpay_payment_id: str,
      razorpay_order_id: str,
      razorpay_signature: str,
      order_id: int
    }

    This endpoint verifies the signature using your key secret and, if valid,
    marks the corresponding Order as paid (idempotent) and enqueues invoice send.
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return HttpResponseBadRequest('Invalid JSON')

    payment_id = payload.get('razorpay_payment_id')
    order_id = payload.get('order_id')
    razor_order_id = payload.get('razorpay_order_id')
    signature = payload.get('razorpay_signature')

    if not (payment_id and razor_order_id and signature and order_id):
        return HttpResponseBadRequest('Missing fields')

    # Shortcut for mock provider in local tests
    # If using a mock provider for local tests, accept and mark paid without signature checks
    provider_name = getattr(settings, 'PAYMENT_PROVIDER', 'razorpay')
    if provider_name == 'mock':
        try:
            from .models import Order
            order = Order.objects.get(id=order_id)
            if order.payment_status != 'paid':
                order.payment_status = 'paid'
                order.transaction_id = payment_id
                order.save(update_fields=['payment_status', 'transaction_id'])
                try:
                    from store.tasks import send_order_email
                    send_order_email.delay(order.id, 'invoice', f'Invoice - {settings.SITE_NAME} - {order.order_number}', order.user.email, settings.SITE_URL)
                except Exception:
                    logger.exception('Failed to enqueue send_order_email task during mock verify for order %s', order.order_number)
                    try:
                        from .views import _send_order_email
                        _send_order_email(order, 'invoice', f'Invoice - {settings.SITE_NAME} - {order.order_number}', order.user.email, request=None)
                    except Exception:
                        logger.exception('Synchronous invoice send failed during mock verify for order %s', order.order_number)
            return JsonResponse({'status': 'ok'})
        except Exception:
            logger.exception('Order not found during mock verify for id %s', order_id)
            return HttpResponse('Order not found', status=404)

    # Verify signature using razorpay SDK utility if available, otherwise manual HMAC
    try:
        import razorpay
        client = razorpay.Client(auth=(getattr(settings, 'RAZORPAY_KEY_ID', ''), getattr(settings, 'RAZORPAY_KEY_SECRET', '')))
        client.utility.verify_payment_signature({
            'razorpay_order_id': razor_order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature,
        })
    except Exception:
        # Manual HMAC fallback using key secret
        secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')
        if not secret:
            logger.exception('No razorpay key secret configured for signature verification')
            return HttpResponse('Verification failed', status=500)
        expected = hmac.new(secret.encode('utf-8'), f"{razor_order_id}|{payment_id}".encode('utf-8'), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            logger.warning('Invalid payment signature (manual verify) for order_id %s', order_id)
            return HttpResponseBadRequest('Invalid signature')

    # Find the order and update idempotently
    try:
        from .models import Order
        order = Order.objects.get(id=order_id)
    except Exception:
        logger.exception('Order not found during verify for id %s', order_id)
        return HttpResponse('Order not found', status=404)

    try:
        # Only update if not already paid
        if order.payment_status != 'paid':
            # Optionally verify amounts match by fetching payment details from Razorpay
            order.payment_status = 'paid'
            order.transaction_id = payment_id
            order.save(update_fields=['payment_status', 'transaction_id'])
            try:
                from store.tasks import send_order_email
                send_order_email.delay(order.id, 'invoice', f'Invoice - {settings.SITE_NAME} - {order.order_number}', order.user.email, settings.SITE_URL)
            except Exception:
                logger.exception('Failed to enqueue send_order_email task during verify for order %s', order.order_number)
                try:
                    from .views import _send_order_email
                    _send_order_email(order, 'invoice', f'Invoice - {settings.SITE_NAME} - {order.order_number}', order.user.email, request=None)
                except Exception:
                    logger.exception('Synchronous invoice send failed during verify for order %s', order.order_number)
    except Exception:
        logger.exception('Error marking order paid during verify for order id %s', order_id)
        return HttpResponse('Error', status=500)

    return JsonResponse({'status': 'ok'})
