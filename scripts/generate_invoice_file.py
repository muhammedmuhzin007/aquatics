import os, sys, traceback
os.environ.setdefault('DJANGO_SETTINGS_MODULE','fishy_friend_aquatics.settings')
try:
    import django
    django.setup()
    from store.models import Order
    from store.views import generate_invoice_pdf

    o = Order.objects.order_by('-created_at').first()
    if not o:
        print('No orders found; nothing to generate')
        sys.exit(0)
    print('Generating invoice for order', o.order_number)
    pdf_bytes = generate_invoice_pdf(o)
    if not pdf_bytes:
        print('PDF generation returned None')
        sys.exit(1)
    out_path = f'scripts/invoice-{o.order_number}.pdf'
    with open(out_path, 'wb') as f:
        f.write(pdf_bytes)
    print('Wrote invoice to', out_path)
except Exception:
    traceback.print_exc()
    sys.exit(1)
