from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0050_move_weight_to_combo"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="delivery_charge",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=8),
        ),
        migrations.AddField(
            model_name="order",
            name="total_weight",
            field=models.DecimalField(decimal_places=3, default=0, max_digits=8),
        ),
        migrations.AddField(
            model_name="order",
            name="shipping_state",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="order",
            name="shipping_pincode",
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
