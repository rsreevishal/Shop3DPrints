# Generated by Django 3.1 on 2020-09-23 03:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_auto_20200923_0345'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='category',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='api.subcategory'),
            preserve_default=False,
        ),
    ]