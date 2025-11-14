import os,sys,traceback
os.environ.setdefault('DJANGO_SETTINGS_MODULE','fishy_friend_aquatics.settings')
try:
    import django
    django.setup()
    from django.conf import settings
    from django.core.mail import send_mail
    from store.models import Order
    from store.views import _send_order_email

    print('EMAIL_BACKEND=', getattr(settings,'EMAIL_BACKEND',None))
    print('EMAIL_HOST=', getattr(settings,'EMAIL_HOST',None))
    print('EMAIL_PORT=', getattr(settings,'EMAIL_PORT',None))
    print('EMAIL_USE_TLS=', getattr(settings,'EMAIL_USE_TLS',None))
    print('EMAIL_USE_SSL=', getattr(settings,'EMAIL_USE_SSL',None))
    print('EMAIL_HOST_USER=', getattr(settings,'EMAIL_HOST_USER',None))
    print('DEFAULT_FROM_EMAIL=', getattr(settings,'DEFAULT_FROM_EMAIL',None))

    test_to = getattr(settings,'EMAIL_HOST_USER',None)
    if not test_to:
        print('No EMAIL_HOST_USER configured; aborting test send.')
        sys.exit(0)

    print('\nAttempting simple send_mail to', test_to)
    try:
        res = send_mail('SMTP test from project','If you receive this, SMTP is configured.',(getattr(settings,'DEFAULT_FROM_EMAIL', 'noreply@aquafishstore.com')),[test_to], fail_silently=False)
        print('send_mail returned:', res)
    except Exception:
        print('send_mail exception:')
        traceback.print_exc()

    o = Order.objects.order_by('-created_at').first()
    if not o:
        print('No orders found; skipping invoice send test')
        sys.exit(0)
    print('\nAttempting invoice send for order', o.order_number, 'to', o.user.email)
    try:
        _send_order_email(o, 'invoice', f'Test Invoice - {o.order_number}', o.user.email, request=None)
        print('invoice helper completed (no exception)')
    except Exception:
        print('invoice helper exception:')
        traceback.print_exc()

except Exception:
    traceback.print_exc()
    sys.exit(1)
