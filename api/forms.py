from django.forms import ModelForm, DateInput, Form, CharField, IntegerField, Textarea

from api.models import Purchase, Student, Instructor, Event, Project, Exam, ExamGrade


class RegistrationForm(ModelForm):
    class Meta:
        model = Student
        exclude = ['django_user']


class PurchaseForm(Form):
    course = IntegerField()
    batch = CharField()
    date = CharField()
    time = CharField()


class EventForm(ModelForm):
    class Meta:
        model = Event
        # datetime-local is a HTML5 input type, format to make date time show on fields
        widgets = {
            'start_time': DateInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'end_time': DateInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }
        exclude = ['user']

    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        # input_formats to parse HTML5 datetime-local input to datetime field
        self.fields['start_time'].input_formats = ('%Y-%m-%dT%H:%M',)
        self.fields['end_time'].input_formats = ('%Y-%m-%dT%H:%M',)


class InstructorForm(ModelForm):
    class Meta:
        model = Instructor
        exclude = ['is_verified', 'django_user']


class ProjectForm(ModelForm):
    class Meta:
        model = Project
        exclude = ['course']


class ExamForm(ModelForm):
    class Meta:
        model = Exam
        exclude = ['course']


class ExamGradeForm(ModelForm):
    def __init__(self, filter_course_id, *args, **kwargs):
        super(ExamGradeForm, self).__init__(*args, **kwargs)
        self.fields['exam'].queryset = Exam.objects.filter(course=filter_course_id)

    class Meta:
        model = ExamGrade
        exclude = ['student']
