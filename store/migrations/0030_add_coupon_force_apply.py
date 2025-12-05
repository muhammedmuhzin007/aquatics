from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0029_contactgallerymedia'),
    ]

    operations = [
        migrations.AddField(
            model_name='coupon',
            name='force_apply',
            field=models.BooleanField(default=False, help_text='If set, this coupon bypasses normal validity checks when applied (admin use only)'),
        ),
    ]
