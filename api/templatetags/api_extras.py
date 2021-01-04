from datetime import datetime
from typing import Union

from django import template
from django.utils import timezone

from api.models import Exam, ExamGrade, Project, ProjectSubmission, Student, AcademyUser, Event, Attendance, \
    StudentInstructor, Instructor

register = template.Library()


@register.filter()
def grade(assignment: Exam, me: Student):
    try:
        return f'{assignment.examgrade_set.get(student=me).marks}/{assignment.total_points}'

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


@register.filter(name='local_time')
def local_time(t, me):
    at = datetime.combine(datetime.now(), t).replace(tzinfo=timezone.utc).astimezone(tz=me.timezone).time()
    return at.strftime("%I:%M %p")


@register.filter(name="course_complete_status")
def course_complete_status(enrollment):
    events = Event.objects.filter(enrollment=enrollment)
    for e in events:
        if e.status == Attendance.present:
            continue
        else:
            return False
    return True


@register.filter(name="course_link")
def course_link(enrollment):
    if StudentInstructor.objects.filter(enrollment=enrollment).exists():
        instructor = StudentInstructor.objects.get(enrollment=enrollment).instructor
        return instructor.class_link if instructor.class_link is not None else ""
    else:
        return ""


@register.filter(name="user_name")
def user_name(user):
    me = AcademyUser.get_for(user)
    if isinstance(me, Student):
        return f"{me.student_first_name} {me.student_last_name}"
    elif isinstance(me, Instructor):
        return f"{me.django_user.first_name} {me.django_user.last_name}"


@register.filter(name="my_pk")
def my_pk(user):
    me = AcademyUser.get_for(user)
    return me.pk
