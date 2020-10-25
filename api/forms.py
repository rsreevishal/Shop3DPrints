from django.forms import ModelForm

from api.models import Purchase, Student


class RegistrationForm(ModelForm):
    class Meta:
        model = Student
        exclude = ['django_user']


class PurchaseForm(ModelForm):
    class Meta:
        model = Purchase
        exclude = ['student', 'stripe_id', 'confirmed']
