from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0024_alter_contactinfo_options_blogpost'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='provider_order_id',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
    ]
