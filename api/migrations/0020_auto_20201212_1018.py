# Generated by Django 3.1.1 on 2020-12-12 10:18

import django.core.validators
from django.db import migrations, models
import re


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0019_course_price_usd'),
    ]

    operations = [
        migrations.AlterField(
            model_name='enrollment',
            name='days',
            field=models.CharField(max_length=13, validators=[django.core.validators.RegexValidator(re.compile('^\\d+(?:\\,\\d+)*\\Z'), code='invalid', message='Enter only digits separated by commas.')]),
        ),
    ]
