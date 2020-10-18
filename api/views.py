import json
from django.contrib.auth import login as django_login, logout as django_logout, authenticate
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse

from django.conf import settings
from api.forms import RegistrationForm
from api.models import AcademyUser, Category, Course, Enrollment, Student, Subcategory

from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.core.mail import send_mail


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


def student_progress(request):
    me = AcademyUser.get_for(request.user)
    enrollments = Enrollment.objects.filter(student=me)

    return standard_view('student/progress.html', {
        'enrollments': enrollments
    })(request)


def student_profile(request):
    me = AcademyUser.get_for(request.user)

    if request.method == 'POST':
        form = RegistrationForm(request.POST, instance=me)
        form.save()

    return standard_view('student/profile.html')(request)


def login(request):
    user: User = authenticate(username=request.POST['email'], password=request.POST['password'])
    if user and user.is_authenticated and user.is_active:
        django_login(request, user)
        return HttpResponseRedirect(reverse('student'))

    else:
        return HttpResponse(json.dumps({'success': False}))


def register(request):
    form = RegistrationForm(request.POST)
    print(form.errors)
    student = form.save(commit=False)
    user = User.objects.create_user(username=request.POST['email'], password=request.POST['password'])
    user.is_active = False
    student.django_user = user
    user.save()
    student.save()
    form.save_m2m()

    current_site = get_current_site(request)
    mail_subject = 'Activate your CMS Online Academy account.'
    token = account_activation_token.make_token(user)
    message = render_to_string('acc_active_email.html', {
        'user': student.student_first_name + ' ' + student.student_last_name,       # Add full name property in students model
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': token,
    })
    email_from = settings.EMAIL_HOST_USER
    to_email = [request.POST['email']]
    send_mail(mail_subject, message, email_from, to_email)
    return HttpResponse('Please confirm your email address to complete the registration')


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        django_login(request, user)
        return HttpResponseRedirect(reverse('student'))
    else:
        return HttpResponse('Activation link is invalid!')


def logout(request):
    django_logout(request)
    return HttpResponseRedirect(reverse('index'))
