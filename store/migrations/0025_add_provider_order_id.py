from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0024_alter_contactinfo_options_blogpost'),
    ]

    # This migration previously attempted to add `provider_order_id`, but the
    # same field was already added by migration 0021. Keep this migration as
    # a no-op to avoid duplicate-column errors in test and CI databases.
    operations = []
