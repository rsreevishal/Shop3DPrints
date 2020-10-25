# Generated by Django 3.1.1 on 2020-10-25 22:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0018_auto_20201014_0232'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='price_usd',
            field=models.PositiveSmallIntegerField(default=10, help_text='Price in dollars'),
            preserve_default=False,
        ),
    ]