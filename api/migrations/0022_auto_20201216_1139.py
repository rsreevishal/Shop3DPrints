# Generated by Django 3.1.1 on 2020-12-16 11:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0021_auto_20201216_0858'),
    ]

    operations = [
        migrations.CreateModel(
            name='AvailableDays',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.IntegerField(choices=[(0, 'Sunday'), (1, 'Monday'), (2, 'Tuesday'), (3, 'Wednesday'), (4, 'Thursday'), (5, 'Friday'), (6, 'Saturday')])),
                ('available', models.BooleanField(blank=True, default=True, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='timerange',
            name='available',
            field=models.BooleanField(blank=True, default=True, null=True),
        ),
    ]
