from datetime import datetime
from typing import Union

from django import template
from django.utils import timezone

from api.models import Customer, AcademyUser, ServiceProvider

register = template.Library()


@register.filter
def index(indexable, i):
    return indexable[i]


@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


@register.filter(name="user_name")
def user_name(user):
    me = AcademyUser.get_for(user)
    if isinstance(me, Customer):
        return f"{me.first_name} {me.last_name}"
    elif isinstance(me, ServiceProvider):
        return f"{me.django_user.first_name} {me.django_user.last_name}"


@register.filter(name="my_pk")
def my_pk(user):
    me = AcademyUser.get_for(user)
    return me.pk


@register.filter(name="status_class")
def status_class(status_id):
    status = ['table-primary', 'table-danger', 'table-warning', 'table-secondary', 'table-success', 'table-dark']
    return status[int(status_id)]


@register.filter(name="status_name")
def status_name(status_id):
    status = ['Completed', 'Cancelled', 'Quoted', 'Pending', 'Shipped', 'Paid']
    return status[int(status_id)]
