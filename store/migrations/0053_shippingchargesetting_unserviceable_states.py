from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0052_shippingchargesetting'),
    ]

    operations = [
        migrations.AddField(
            model_name='shippingchargesetting',
            name='unserviceable_states',
            field=models.TextField(
                blank=True,
                default='',
                help_text='List Indian states where delivery is currently unavailable.',
            ),
        ),
    ]
