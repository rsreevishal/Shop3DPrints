# Generated by Django 3.1.1 on 2020-12-28 13:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_auto_20201228_0816'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchase',
            name='payment_method',
            field=models.IntegerField(choices=[(0, 'Full Payment'), (1, 'Per Class Payment'), (2, 'Free Trail')], default=0),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='purchase',
            unique_together={('student', 'course', 'payment_method')},
        ),
    ]