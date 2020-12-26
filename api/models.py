from django.contrib.auth.models import User, AnonymousUser
from django.core.validators import validate_comma_separated_integer_list, MinValueValidator, MaxValueValidator
from django.db import models
from django.urls import reverse
from django.contrib.auth.models import Group


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
    student_first_name = models.CharField(max_length=25)
    student_last_name = models.CharField(max_length=25)
    parent_first_name = models.CharField(max_length=25)
    parent_last_name = models.CharField(max_length=25)

    grade = models.PositiveSmallIntegerField()
    country = models.PositiveSmallIntegerField()  # This should probably use country code instead of the number.
    phone_number = models.CharField(max_length=50)

    @property
    def name(self):
        return self.django_user.username

    def __str__(self):
        return f'{self.student_first_name} {self.student_last_name} ({self.django_user.username})'


class Speciality(models.Model):
    speciality_name = models.CharField(max_length=50)

    def __str__(self):
        return self.speciality_name


class SpecialityLevel(models.Model):
    level = models.IntegerField()
    level_name = models.CharField(max_length=25)

    def __str__(self):
        return self.level_name


class Day(models.IntegerChoices):
    Monday = 0, 'Monday'
    Tuesday = 1, 'Tuesday'
    Wednesday = 2, 'Wednesday'
    Thursday = 3, 'Thursday'
    Friday = 4, 'Friday'
    Saturday = 5, 'Saturday',
    Sunday = 6, 'Sunday'


class AvailableDays(models.Model):
    day = models.IntegerField(choices=Day.choices, unique=True)
    available = models.BooleanField()

    def __str__(self):
        return f"{self.day}-{self.available}"


class AvailableTimes(models.Model):
    start = models.TimeField()
    end = models.TimeField()
    available = models.BooleanField()

    class Meta:
        unique_together = [['start', 'end']]

    def __str__(self):
        return f"{self.start}-{self.end} = {self.available}"


class Instructor(AcademyUser):
    name = models.CharField(max_length=50)
    education_description = models.CharField(max_length=500)
    skill_description = models.CharField(max_length=500)
    project_description = models.CharField(max_length=500)
    has_laptop = models.BooleanField(default=False)
    comfortable_teaching = models.BooleanField(default=False)
    country = models.PositiveSmallIntegerField()
    phone_number = models.CharField(max_length=50)
    is_verified = models.BooleanField(default=False)

    @classmethod
    def create(cls, data):
        user = User.objects.create_user(username=data['email'], email=data['email'],
                                        password=data['password'], first_name=data['first_name'],
                                        last_name=data['last_name'])
        user.is_active = False
        user.save()
        instructor = cls(django_user=user, name=user.username, education_description=data["education_description"],
                         skill_description=data["skill_description"], project_description=data["project_description"],
                         has_laptop=data["has_laptop"], comfortable_teaching=data["comfortable_teaching"],
                         country=data["countryCode"], phone_number=str(data["contact"])
                         )
        instructor_group = Group.objects.get(name="Instructor")
        instructor_group.user_set.add(user)
        instructor.django_user = user
        instructor.save()
        # data format: 'speciality': [[1, 2], [2, 2], [3, 2]]
        for sp in data["speciality"]:
            sp_pk = sp[0]  # speciality pk
            spl_pk = sp[1]  # speciality_level pk
            speciality = Speciality.objects.get(pk=sp_pk)
            speciality_level = SpecialityLevel.objects.get(pk=spl_pk)
            instructor_speciality = InstructorSpeciality(instructor=instructor, speciality=speciality,
                                                         speciality_level=speciality_level)
            instructor_speciality.save()
        for ad in data["available_days"]:
            for at in data["available_times"]:
                time = AvailableTimes.objects.get(pk=at)
                instructor_time_slot = InstructorTimeSlot(instructor=instructor, day=ad, start=time.start, end=time.end)
                instructor_time_slot.save()
        return instructor

    def __str__(self):
        return self.name


class InstructorSpeciality(models.Model):
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    speciality = models.ForeignKey(Speciality, on_delete=models.CASCADE)
    speciality_level = models.ForeignKey(SpecialityLevel, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.instructor},{self.speciality_level},{self.speciality} person"


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
    total_price_usd = models.PositiveSmallIntegerField(help_text='Price in dollars')
    per_class_price_usd = models.PositiveSmallIntegerField(help_text='Price in dollars')
    description = models.TextField()
    highlights = models.TextField(help_text='Put each item on its own line')
    prerequisites = models.TextField(help_text='Put each item on its own line')
    sessions = models.TextField(help_text='Put each item on its own line')
    thumbnail = models.ImageField(upload_to="thumbnail/", blank=True, default=None, null=True)
    course_link = models.URLField(help_text="Enter the course link", blank=True, default=None, null=True)
    total_days = models.IntegerField()

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


class CourseTimeSlot(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    day = models.IntegerField(choices=Day.choices)
    start = models.TimeField()
    end = models.TimeField()

    def __str__(self):
        return f"{self.course.name}: {self.start}-{self.end}"


class InstructorTimeSlot(models.Model):
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    day = models.IntegerField(choices=Day.choices)
    start = models.TimeField()
    end = models.TimeField()

    def __str__(self):
        return f"{self.day}, {self.start}, {self.end}"


class CourseInstructor(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.course.name} - {self.instructor.name}"


class Project(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField(max_length=512)
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
    description = models.TextField(max_length=512)
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


class Purchase(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    batch = models.CharField(max_length=16)
    course_datetime = models.DateTimeField()
    stripe_id = models.CharField(max_length=128)
    confirmed = models.BooleanField(default=False)


class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE)
    days = models.CharField(max_length=13, validators=[validate_comma_separated_integer_list])
    start_time = models.TimeField()
    end_time = models.TimeField()

    def get_days_display(self):
        return ', '.join(
            map(lambda day: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][int(day)], self.days.split(',')))

    def __str__(self):
        return f'{self.student.name} in {self.course.name}'


class Attendance(models.IntegerChoices):
    present = 0, 'PRESENT'
    absent = 1, 'ABSENT'
    other = 2, 'OTHER'


class PaymentMethod(models.IntegerChoices):
    full_payment = 0
    per_class_payment = 1


class Event(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.IntegerField(choices=Attendance.choices, null=True, default=None, blank=True)
    updated_by = models.ForeignKey(Instructor, null=True, default=None, blank=True, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(null=True, default=None, blank=True)
    enrollment = models.ForeignKey(Enrollment, null=True, default=None, blank=True, on_delete=models.CASCADE)
    payment_method = models.IntegerField(choices=PaymentMethod.choices, null=True, default=None, blank=True)
    total_amount = models.PositiveSmallIntegerField(help_text="Price in usd", null=True, default=None, blank=True)
    amount_paid = models.PositiveSmallIntegerField(help_text="Price in usd", null=True, default=None, blank=True)
    paid_at = models.DateTimeField(null=True, default=None, blank=True)

    @property
    def get_html_url(self):
        url = reverse('event_edit', args=(self.id,))
        return f'<p> {self.title} </p>'

    def __str__(self):
        return self.title


class StudentInstructor(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.enrollment.student.name}-{self.instructor.name}'


class CourseMaterial(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=500)
    material_link = models.URLField()
    uploader = models.ForeignKey(Instructor, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.course.name}-{self.material_link}'
