from datetime import time, timedelta, datetime

from django.utils import timezone
from django.contrib.auth.models import User, AnonymousUser
from django.core.validators import validate_comma_separated_integer_list, MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import Group
import pytz
from timezone_field import TimeZoneField
from django.db.models.signals import post_save


class AcademyUser(models.Model):
    class Meta:
        abstract = True

    django_user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    timezone = TimeZoneField(default='UTC', null=True, blank=True,
                             choices=[
                                 (tz, tz) for tz in pytz.common_timezones
                             ])
    is_tz_set = models.BooleanField(default=False, null=True, blank=True)

    @classmethod
    def get_for(cls, user: User):
        if isinstance(user, AnonymousUser):
            return None

        try:
            return Customer.objects.get(django_user=user)
        except Customer.DoesNotExist:
            try:
                return ServiceProvider.objects.get(django_user=user)
            except ServiceProvider.DoesNotExist:
                pass

    def __str__(self):
        return f'{self.django_user.username}'


class Customer(AcademyUser):
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)
    country = models.PositiveSmallIntegerField()  # This should probably use country code instead of the number.
    phone_number = models.CharField(max_length=50)
    address = models.CharField(max_length=200)

    @property
    def name(self):
        return self.django_user.username

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.django_user.username})'


class ServiceProvider(AcademyUser):
    name = models.CharField(max_length=50)
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
        service_provider = cls(django_user=user, name=user.username,
                               country=data["countryCode"], phone_number=str(data["contact"])
                               )
        service_provider_group = Group.objects.get(name="ServiceProvider")
        service_provider_group.user_set.add(user)
        service_provider.django_user = user
        service_provider.save()
        return service_provider

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=64)
    thumbnail = models.ImageField(upload_to="thumbnail/", blank=True, default=None, null=True)

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


class Product(models.Model):
    name = models.CharField(max_length=50)
    category = models.ForeignKey(Subcategory, on_delete=models.CASCADE)
    total_price_usd = models.PositiveSmallIntegerField(help_text='Price in dollars')
    description = models.TextField(max_length=512)
    thumbnail = models.ImageField(upload_to="thumbnail/", blank=True, default=None, null=True)

    def __str__(self):
        return self.name


class OrderStatus(models.IntegerChoices):
    pending = 0
    accepted = 1
    rejected = 2


class Purchase(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    datetime = models.DateTimeField()
    stripe_id = models.CharField(max_length=128)
    confirmed = models.BooleanField(default=False)


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE)
    order_status = models.IntegerField(choices=OrderStatus.choices)

