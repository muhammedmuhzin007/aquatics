from django.db import migrations, models
import decimal


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0051_order_delivery_charge'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShippingChargeSetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(default='default', editable=False, max_length=32, unique=True)),
                ('kerala_rate', models.DecimalField(decimal_places=2, default=decimal.Decimal('60.00'), max_digits=8)),
                ('default_rate', models.DecimalField(decimal_places=2, default=decimal.Decimal('100.00'), max_digits=8)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Shipping Charge Setting',
                'verbose_name_plural': 'Shipping Charge Settings',
            },
        ),
    ]
