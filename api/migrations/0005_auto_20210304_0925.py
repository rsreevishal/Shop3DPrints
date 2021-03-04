# Generated by Django 3.1.1 on 2021-03-04 09:25

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_auto_20210304_0847'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='cancel_reason',
            field=models.CharField(max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='order_status',
            field=models.IntegerField(choices=[(0, 'Completed'), (1, 'Cancelled'), (2, 'Quoted'), (3, 'Pending'), (5, 'Shipped')]),
        ),
        migrations.AlterField(
            model_name='order',
            name='ordered_on',
            field=models.DateTimeField(default=datetime.datetime(2021, 3, 4, 9, 25, 8, 787201, tzinfo=utc)),
        ),
    ]