from django.forms import ModelForm, DateInput, Form, CharField, IntegerField, Textarea

from api.models import Customer, ServiceProvider


class RegistrationForm(ModelForm):
    class Meta:
        model = Customer
        exclude = ['django_user']


class PurchaseForm(Form):
    product = IntegerField()
    date = CharField()
    time = CharField()


class ServiceProviderForm(ModelForm):
    class Meta:
        model = ServiceProvider
        exclude = ['is_verified', 'django_user']