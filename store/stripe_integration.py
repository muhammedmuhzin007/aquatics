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
def create_stripe_payment(request, order_id):
    """Create a Stripe PaymentIntent for the given Order and return client data."""
    try:
        from .models import Order
        from store.payments import get_payment_provider
    except Exception:
        return HttpResponseBadRequest('Order model unavailable')

    order = get_object_or_404(Order, id=order_id, user=request.user)

    try:
        provider = get_payment_provider(getattr(settings, 'PAYMENT_PROVIDER', 'stripe'))
        data = provider.create_order(order)
    except Exception as exc:
        logger.exception('Failed to create provider order for order %s: %s', getattr(order, 'order_number', order_id), exc)
        return HttpResponse('Failed to create provider order', status=502)

    # Optionally save provider ids to order
    try:
        if 'payment_intent_id' in data:
            order.provider_order_id = data.get('payment_intent_id')
            order.save(update_fields=['provider_order_id'])
    except Exception:
        logger.exception('Failed to save provider id')

    return JsonResponse(data)


@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhooks; verify signature and mark orders paid."""
    try:
        from .models import Order
        from store.payments import get_payment_provider
    except Exception:
        return HttpResponseBadRequest('Models unavailable')

    provider = get_payment_provider(getattr(settings, 'PAYMENT_PROVIDER', 'stripe'))
    ok, result = provider.handle_webhook(request)
    if not ok:
        logger.warning('Stripe webhook verification failed: %s', result)
        return HttpResponseBadRequest('Invalid webhook')

    event = result
    # Handle payment_intent.succeeded
    ev = event.get('type')
    if ev == 'payment_intent.succeeded':
        try:
            intent = event['data']['object']
            pid = intent.get('id')
            # Find order by provider_order_id
            try:
                order = Order.objects.get(provider_order_id=pid)
            except Order.DoesNotExist:
                logger.warning('Order for provider id %s not found', pid)
                return HttpResponse('Order not found', status=404)

            if order.payment_status != 'paid':
                order.payment_status = 'paid'
                order.transaction_id = intent.get('charges', {}).get('data', [{}])[0].get('id')
                order.save(update_fields=['payment_status', 'transaction_id'])
                try:
                    from store.tasks import send_order_email
                    send_order_email.delay(order.id, 'invoice', f'Invoice - {settings.SITE_NAME} - {order.order_number}', order.user.email, settings.SITE_URL)
                except Exception:
                    logger.exception('Failed to enqueue invoice email for order %s', order.order_number)
        except Exception:
            logger.exception('Error processing stripe payment_intent.succeeded webhook')
            return HttpResponse('Error', status=500)

    return HttpResponse('OK')


@csrf_exempt
def verify_stripe_payment(request):
    """Verify payment returned by Stripe client (client may send payment_intent id).

    Expected JSON body: { payment_intent_id: str, order_id: int }
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return HttpResponseBadRequest('Invalid JSON')

    pid = payload.get('payment_intent_id')
    order_id = payload.get('order_id')

    if not pid or not order_id:
        return HttpResponseBadRequest('Missing fields')

    try:
        from store.payments import get_payment_provider
        provider = get_payment_provider(getattr(settings, 'PAYMENT_PROVIDER', 'stripe'))
        ok = provider.verify_payment({'payment_intent_id': pid})
        if not ok:
            return HttpResponse('Verification failed', status=400)

        # Mark order paid
        from .models import Order
        order = Order.objects.get(id=order_id)
        if order.payment_status != 'paid':
            order.payment_status = 'paid'
            order.transaction_id = pid
            order.save(update_fields=['payment_status', 'transaction_id'])
            try:
                from store.tasks import send_order_email
                send_order_email.delay(order.id, 'invoice', f'Invoice - {settings.SITE_NAME} - {order.order_number}', order.user.email, settings.SITE_URL)
            except Exception:
                logger.exception('Failed to enqueue invoice email during stripe verify for order %s', order.order_number)

        return JsonResponse({'status': 'ok'})
    except Exception:
        logger.exception('Error verifying stripe payment')
        return HttpResponse('Error', status=500)
