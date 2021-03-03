from django.contrib.auth.models import User, AnonymousUser
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import Group
import pytz
from timezone_field import TimeZoneField
from datetime import datetime
from django.utils import timezone


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
    cost = models.FloatField()
    thumbnail = models.ImageField(upload_to="thumbnail/", blank=True, default=None, null=True)

    @property
    def slug(self):
        return self.name.split(' ')[0].lower()

    @property
    def image(self):
        return f'images/{self.slug}.png'

    def __str__(self):
        return self.name


class Material(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=200)
    cost = models.FloatField()

    def __str__(self):
        return f"{self.name}, cost: {self.cost}"


class CategoryMaterial(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.category.name}-{self.material.name}"


class Density(models.Model):
    value = models.FloatField()
    cost = models.FloatField()

    def __str__(self):
        return f"{self.value}%, cost: {self.cost}"


class Unit(models.TextChoices):
    microns = 'microns', 'microns'
    mm = 'mm', 'mm'
    cm = 'cm', 'cm'


class LayerHeight(models.Model):
    start_value = models.FloatField()
    end_value = models.FloatField()
    unit = models.CharField(max_length=50, choices=Unit.choices)
    cost = models.FloatField()

    def __str__(self):
        return f"{self.start_value}-{self.end_value}, cost: {self.cost}"


def validate_file_extension(value):
    if not value.name.endswith('.pdf'):
        raise ValidationError(u'Error message')


class Product(models.Model):
    name = models.CharField(max_length=50)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    density = models.ForeignKey(Density, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    layer_height = models.ForeignKey(LayerHeight, on_delete=models.CASCADE)
    total_price = models.PositiveSmallIntegerField(help_text='Price of the product')
    description = models.TextField(max_length=512)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    stl_file = models.FileField(upload_to="stl/", blank=True, default=None, null=True,
                                validators=[validate_file_extension])
    created_on = models.DateTimeField(null=True)

    @staticmethod
    def parse_request(request):
        return Product(name=request.POST.get('name'), description=request.POST.get('description'),
                       density=Density.objects.get(id=int(request.POST.get('density'))),
                       material=Material.objects.get(id=int(request.POST.get('material'))),
                       layer_height=LayerHeight.objects.get(id=int(request.POST.get('layer_height'))),
                       category=Category.objects.get(id=int(request.POST.get('category'))),
                       stl_file=request.FILES['stl_file'], created_on=timezone.now())

    def get_total_price(self):
        def value(val):  # helper function
            return val if val else 0.0

        return value(self.category.cost) + value(self.density.cost) + value(self.material.cost) \
               + value(self.layer_height.cost)

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
