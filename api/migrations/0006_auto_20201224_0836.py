# Generated by Django 3.1.1 on 2020-12-24 08:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_auto_20201224_0806'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exam',
            name='description',
            field=models.TextField(max_length=512),
        ),
        migrations.AlterField(
            model_name='project',
            name='description',
            field=models.TextField(max_length=512),
        ),
    ]
