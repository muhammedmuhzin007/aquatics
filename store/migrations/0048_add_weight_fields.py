from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0047_plantmedia"),
    ]

    operations = [
        migrations.AddField(
            model_name="accessory",
            name="weight",
            field=models.DecimalField(blank=True, decimal_places=2, help_text="Weight in grams (optional)", max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name="fish",
            name="weight",
            field=models.DecimalField(blank=True, decimal_places=2, help_text="Average weight in grams (optional)", max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name="limitedoffer",
            name="weight",
            field=models.DecimalField(blank=True, decimal_places=2, help_text="Weight in grams (optional)", max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name="plant",
            name="weight",
            field=models.DecimalField(blank=True, decimal_places=2, help_text="Weight in grams (optional)", max_digits=8, null=True),
        ),
    ]
