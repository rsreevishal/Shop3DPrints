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
        data.get(student=me)
        return 'complete'

    except ProjectSubmission.DoesNotExist:
        return 'incomplete'

    except ExamGrade.DoesNotExist:
        return 'incomplete'


@register.filter
def index(indexable, i):
    return indexable[i]
