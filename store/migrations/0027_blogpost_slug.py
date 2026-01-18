# Generated migration to add slug field to BlogPost

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0054_rename_excerpt_blogpost_sub_title_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='blogpost',
            name='slug',
            field=models.SlugField(max_length=260, null=True, unique=True),
            preserve_default=False,
        ),
    ]
