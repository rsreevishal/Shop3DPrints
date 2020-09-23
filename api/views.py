from django.contrib.auth import login as django_login, logout as django_logout
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse

from api.forms import RegistrationForm
from api.models import AcademyUser, Category, Course, Enrollment, Student, Subcategory


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
            'all_categories': Category.objects.all(),
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


def courses_offered(request, category_id):
    category = Category.objects.get(id=category_id)

    return standard_view('landing/courses-offered.html', {
        'category': category,
    })(request)


def course_details(request, course_id):
    course = Course.objects.get(id=course_id)

    return standard_view('landing/course-details.html', {
        'course': course,
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


def register(request):
    form = RegistrationForm(request.POST)
    print(form.errors)
    student = form.save(commit=False)

    user = User.objects.create_user(username=request.POST['email'], password=request.POST['password'])
    student.django_user = user

    student.save()
    form.save_m2m()

    django_login(request, user)
    return HttpResponseRedirect(reverse('student'))


def logout(request):
    django_logout(request)
    return HttpResponseRedirect(reverse('index'))
