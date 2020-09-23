from django.contrib.auth.models import User, AnonymousUser
from django.core.validators import validate_comma_separated_integer_list
from django.db import models


class Grade(models.TextChoices):
    Elementary = 'E', '1-5'
    Middle = 'M', '6-8'
    High = 'H', '9-12'


class AcademyUser(models.Model):
    class Meta:
        abstract = True

    django_user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)

    @classmethod
    def get_for(cls, user: User):
        if isinstance(user, AnonymousUser):
            return None

        try:
            return Student.objects.get(django_user=user)
        except Student.DoesNotExist:
            try:
                return Instructor.objects.get(django_user=user)
            except Instructor.DoesNotExist:
                pass

    def __str__(self):
        return f'{self.django_user.username}'


class Student(AcademyUser):
    class Country(models.TextChoices):
        US = 'US', 'United States'
        IN = 'IN', 'India'

    student_first_name = models.CharField(max_length=25)
    student_last_name = models.CharField(max_length=25)
    parent_first_name = models.CharField(max_length=25)
    parent_last_name = models.CharField(max_length=25)

    grade = models.CharField(max_length=1, choices=Grade.choices)
    country = models.CharField(max_length=2, choices=Country.choices)
    phone_number = models.CharField(max_length=50)

    @property
    def name(self):
        return self.django_user.username

    def __str__(self):
        return f'{self.student_first_name} {self.student_last_name} ({self.django_user.username})'


class Instructor(AcademyUser):
    name = models.CharField(max_length=50)

    def __str__(self):
        return f'{self.name} ({self.django_user.username})'


class Category(models.Model):
    name = models.CharField(max_length=64)

    @property
    def slug(self):
        return self.name.split(' ')[0].lower()

    @property
    def image(self):
        return f'images/{self.slug}.png'

    def __str__(self):
        return self.name


class Subcategory(models.Model):
    name = models.CharField(max_length=64)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.name} ({self.category.name})'


class Course(models.Model):
    name = models.CharField(max_length=50)
    category = models.ForeignKey(Subcategory, on_delete=models.CASCADE)
    grade = models.CharField(max_length=1, choices=Grade.choices)
    level = models.PositiveSmallIntegerField()
    description = models.TextField()
    highlights = models.TextField(help_text='Put each item on its own line')
    prerequisites = models.TextField(help_text='Put each item on its own line')
    sessions = models.TextField(help_text='Put each item on its own line')
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)

    @property
    def highlight_list(self):
        return self.highlights.split('\n')

    @property
    def prerequisite_list(self):
        return self.prerequisites.split('\n')

    @property
    def session_list(self):
        return self.sessions.split('\n')

    def __str__(self):
        return self.name


class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    days = models.CharField(max_length=13, validators=[validate_comma_separated_integer_list])
    start_time = models.TimeField()
    end_time = models.TimeField()

    def get_days_display(self):
        return ', '.join(
            map(lambda day: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][int(day)], self.days.split(',')))

    def __str__(self):
        return f'{self.student.name} in {self.course.name}'


# class Timeslot(models.Model):
#     class Day(models.TextChoices):
#         Sunday = 'S', 'Sunday'
#         Monday = 'M', 'Monday'
#         Tuesday = 'T', 'Tuesday'
#         Wednesday = 'W', 'Wednesday'
#         Thursday = 'H', 'Thursday'
#         Friday = 'F', 'Friday'
#         Saturday = 'A', 'Saturday'
#
#     day = models.CharField(max_length=1, choices=Day.choices)
#     start = models.TimeField()
#     end = models.TimeField()


class Project(models.Model):
    name = models.CharField(max_length=128)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class ProjectSubmission(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    file = models.FileField()

    def __str__(self):
        return f'{self.student.name} for {self.project.name}'


class Exam(models.Model):
    name = models.CharField(max_length=128)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    total_points = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.name


class ExamGrade(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    grade = models.PositiveSmallIntegerField()

    def __str__(self):
        return f'{self.student.name} for {self.exam.name}'
