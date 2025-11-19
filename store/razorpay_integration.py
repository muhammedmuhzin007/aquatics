from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.conf import settings
import json

from .models import Order
from .payments import get_payment_provider


def create_razorpay_payment(request, order_id):
    """Create a razorpay order for the given order id and return payload for client."""
    if request.method != 'POST' and request.method != 'GET':
        return HttpResponseBadRequest('Only POST/GET allowed')

    order = get_object_or_404(Order, id=order_id)
    provider = get_payment_provider('razorpay')
    try:
        payload = provider.create_order(order)
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
    return JsonResponse({'success': bool(ok)})


@csrf_exempt
def razorpay_webhook(request):
    """Receive Razorpay webhooks and hand off to provider for verification."""
    provider = get_payment_provider('razorpay')
    ok, event_or_msg = provider.handle_webhook(request)
    if not ok:
        return HttpResponse(status=400)
    # For now, we simply acknowledge the webhook. Downstream processing
    # (fulfillment, payment capture confirmation) can be added here.
    return HttpResponse(status=200)
