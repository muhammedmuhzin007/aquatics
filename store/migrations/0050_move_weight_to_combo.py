from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0049_update_weight_to_kg"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="limitedoffer",
            name="weight",
        ),
        migrations.AddField(
            model_name="combooffer",
            name="weight",
            field=models.DecimalField(
                max_digits=6,
                decimal_places=3,
                null=True,
                blank=True,
                help_text="Total combo weight in kilograms (optional)",
            ),
        ),
    ]
