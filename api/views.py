from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse

from api.models import AcademyUser, Course, Enrollment


def redirect_view(path_name):
    def view(request, **kwargs):
        return HttpResponseRedirect(reverse(path_name))

    return view


def standard_view(template_name, ctx=None):
    if ctx is None:
        ctx = {}

    def view(request, **kwargs):
        template = loader.get_template(template_name)
        context = {
            'me': AcademyUser.get_for(request.user),
            'all_categories': Course.Category.choices,
            **kwargs,
            **ctx,
        }
        return HttpResponse(template.render(context, request))

    return view


def index(request):
    trending = Course.objects.order_by('-enrollment')[:2]
    fresh = Course.objects.order_by('-id')[:3]

    return standard_view('landing/index.html', {
        'trending': trending,
        'fresh': fresh,
    })(request)


def student_courses(request):
    me = AcademyUser.get_for(request.user)
    enrollments = Enrollment.objects.filter(student=me)

    return standard_view('student/courses.html', {
        'enrollments': enrollments
    })(request)


def student_course(request, course_id):
    me = AcademyUser.get_for(request.user)
    enrollment = Enrollment.objects.get(student=me, course_id=course_id)

    return standard_view('student/course.html', {
        'enrollment': enrollment
    })(request)
