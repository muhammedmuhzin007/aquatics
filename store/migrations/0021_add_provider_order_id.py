from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0020_limitedoffer_fish'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='provider_order_id',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
    ]
