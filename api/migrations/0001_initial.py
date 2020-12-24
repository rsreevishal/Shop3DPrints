# Generated by Django 3.1.1 on 2020-12-21 15:50

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import re


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='AvailableDays',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.IntegerField(choices=[(0, 'Sunday'), (1, 'Monday'), (2, 'Tuesday'), (3, 'Wednesday'), (4, 'Thursday'), (5, 'Friday'), (6, 'Saturday')], unique=True)),
                ('available', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
            ],
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('grade', models.CharField(choices=[('E', '1-5'), ('M', '6-8'), ('H', '9-12')], max_length=1)),
                ('level', models.PositiveSmallIntegerField()),
                ('price_usd', models.PositiveSmallIntegerField(help_text='Price in dollars')),
                ('description', models.TextField()),
                ('highlights', models.TextField(help_text='Put each item on its own line')),
                ('prerequisites', models.TextField(help_text='Put each item on its own line')),
                ('sessions', models.TextField(help_text='Put each item on its own line')),
                ('thumbnail', models.ImageField(blank=True, default=None, null=True, upload_to='thumbnail/')),
                ('course_link', models.URLField(blank=True, default=None, help_text='Enter the course link', null=True)),
                ('total_days', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Exam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('total_points', models.PositiveSmallIntegerField()),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.course')),
            ],
        ),
        migrations.CreateModel(
            name='Instructor',
            fields=[
                ('django_user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='auth.user')),
                ('name', models.CharField(max_length=50)),
                ('education_description', models.CharField(max_length=500)),
                ('skill_description', models.CharField(max_length=500)),
                ('project_description', models.CharField(max_length=500)),
                ('has_laptop', models.BooleanField(default=False)),
                ('comfortable_teaching', models.BooleanField(default=False)),
                ('country', models.PositiveSmallIntegerField()),
                ('phone_number', models.CharField(max_length=50)),
                ('is_verified', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.course')),
            ],
        ),
        migrations.CreateModel(
            name='Speciality',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('speciality_name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='SpecialityLevel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.IntegerField()),
                ('level_name', models.CharField(max_length=25)),
            ],
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('django_user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='auth.user')),
                ('student_first_name', models.CharField(max_length=25)),
                ('student_last_name', models.CharField(max_length=25)),
                ('parent_first_name', models.CharField(max_length=25)),
                ('parent_last_name', models.CharField(max_length=25)),
                ('grade', models.PositiveSmallIntegerField()),
                ('country', models.PositiveSmallIntegerField()),
                ('phone_number', models.CharField(max_length=50)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Subcategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.category')),
            ],
        ),
        migrations.CreateModel(
            name='Purchase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('batch', models.CharField(max_length=16)),
                ('date', models.DateTimeField()),
                ('timing', models.CharField(max_length=3)),
                ('stripe_id', models.CharField(max_length=128)),
                ('confirmed', models.BooleanField(default=False)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.course')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.student')),
            ],
        ),
        migrations.CreateModel(
            name='ProjectSubmission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.project')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.student')),
            ],
        ),
        migrations.CreateModel(
            name='InstructorTimeSlot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.IntegerField(choices=[(0, 'Sunday'), (1, 'Monday'), (2, 'Tuesday'), (3, 'Wednesday'), (4, 'Thursday'), (5, 'Friday'), (6, 'Saturday')])),
                ('start', models.TimeField()),
                ('end', models.TimeField()),
                ('instructor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.instructor')),
            ],
        ),
        migrations.CreateModel(
            name='InstructorSpeciality',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('instructor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.instructor')),
                ('speciality', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.speciality')),
                ('speciality_level', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.specialitylevel')),
            ],
        ),
        migrations.CreateModel(
            name='ExamGrade',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('grade', models.PositiveSmallIntegerField()),
                ('exam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.exam')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.student')),
            ],
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Enrollment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('days', models.CharField(max_length=13, validators=[django.core.validators.RegexValidator(re.compile('^\\d+(?:\\,\\d+)*\\Z'), code='invalid', message='Enter only digits separated by commas.')])),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.course')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.student')),
            ],
        ),
        migrations.CreateModel(
            name='CourseTimeSlot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.IntegerField(choices=[(0, 'Sunday'), (1, 'Monday'), (2, 'Tuesday'), (3, 'Wednesday'), (4, 'Thursday'), (5, 'Friday'), (6, 'Saturday')])),
                ('start', models.TimeField()),
                ('end', models.TimeField()),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.course')),
            ],
        ),
        migrations.CreateModel(
            name='CourseInstructor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.course')),
                ('instructor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.instructor')),
            ],
        ),
        migrations.AddField(
            model_name='course',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.subcategory'),
        ),
        migrations.CreateModel(
            name='AvailableTimes',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.TimeField()),
                ('end', models.TimeField()),
                ('available', models.BooleanField()),
            ],
            options={
                'unique_together': {('start', 'end')},
            },
        ),
    ]
