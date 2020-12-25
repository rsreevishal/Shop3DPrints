from typing import Union

from django import template

from api.models import Exam, ExamGrade, Project, ProjectSubmission, Student

register = template.Library()


@register.filter()
def grade(assignment: Exam, me: Student):
    try:
        return f'{assignment.examgrade_set.get(student=me).grade}/{assignment.total_points}'

    except ExamGrade.DoesNotExist:
        return f'--/{assignment.total_points}'


@register.simple_tag()
def status(assignment: Union[Project, Exam], me: Student):
    if isinstance(assignment, Project):
        data = assignment.projectsubmission_set

    else:
        data = assignment.examgrade_set

    try:
        sub = data.get(student=me)
        return ['complete', sub]
    except ProjectSubmission.DoesNotExist:
        return ['incomplete', None]

    except ExamGrade.DoesNotExist:
        return ['incomplete', None]


@register.filter
def index(indexable, i):
    return indexable[i]


@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


@register.filter
def attendance_status(_id):
    status_name = ["Present", "Absent", "Other"]
    if _id is None:
        return "-"
    else:
        return status_name[_id]
