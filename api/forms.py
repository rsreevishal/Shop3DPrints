from django.forms import ModelForm

from api.models import Student


class RegistrationForm(ModelForm):
    class Meta:
        model = Student
        exclude = ['django_user']
