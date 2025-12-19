from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0048_add_weight_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="fish",
            name="weight",
            field=models.DecimalField(blank=True, decimal_places=3, help_text="Average weight in kilograms (optional)", max_digits=6, null=True),
        ),
        migrations.AlterField(
            model_name="accessory",
            name="weight",
            field=models.DecimalField(blank=True, decimal_places=3, help_text="Weight in kilograms (optional)", max_digits=6, null=True),
        ),
        migrations.AlterField(
            model_name="plant",
            name="weight",
            field=models.DecimalField(blank=True, decimal_places=3, help_text="Weight in kilograms (optional)", max_digits=6, null=True),
        ),
        migrations.AlterField(
            model_name="limitedoffer",
            name="weight",
            field=models.DecimalField(blank=True, decimal_places=3, help_text="Weight in kilograms (optional)", max_digits=6, null=True),
        ),
    ]
