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
    name = models.CharField(max_length=50)

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
        return f'{self.name} ({self.django_user.username})'


class Student(AcademyUser):
    class Country(models.TextChoices):
        US = 'US', 'United States'
        IN = 'IN', 'India'

    grade = models.CharField(max_length=1, choices=Grade.choices)
    country = models.CharField(max_length=2, choices=Country.choices)
    parents_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=50)


class Instructor(AcademyUser):
    pass


class Course(models.Model):
    class Category(models.TextChoices):
        Programming = 'P', 'Programming'
        ArtsAndCrafts = 'A', 'Arts & Crafts'
        MusicAndDance = 'M', 'Music & Dance'
        Language = 'L', 'Language'
        Education = 'E', 'Education'
        Games = 'G', 'Games'

    name = models.CharField(max_length=50)
    category = models.CharField(max_length=1, choices=Category.choices)
    grade = models.CharField(max_length=1, choices=Grade.choices)
    level = models.PositiveSmallIntegerField()
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)

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
