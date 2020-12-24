import json
import calendar

import stripe

from django.contrib.auth import login as django_login, logout as django_logout, authenticate
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import loader
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from django.conf import settings
from api.models import AcademyUser, Category, Course, Enrollment, Purchase, SpecialityLevel, Speciality, AvailableDays, \
    Instructor, AvailableTimes, Event, CourseTimeSlot, StudentInstructor, CourseMaterial, InstructorSpeciality, Student, \
    Project, Exam, ExamGrade
from academy_backend import settings
from api.forms import RegistrationForm, PurchaseForm, EventForm, InstructorForm, ProjectForm, ExamForm, ExamGradeForm

from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver
from django_rest_passwordreset.signals import reset_password_token_created, pre_password_reset, post_password_reset
from datetime import datetime, date, timedelta
from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.utils.safestring import mark_safe
from .utils import Calendar
from django.contrib.auth.models import Group


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


def get_next_weekday(day):
    today = datetime.today()
    while today.weekday() != day:
        today += timedelta(1)
    return today


def course_details(request, course_id):
    course = Course.objects.get(id=course_id)
    time_slots = CourseTimeSlot.objects.filter(course=course)
    final_result = []
    for ts in time_slots:
        final_result.append(
            {
                "date": get_next_weekday(ts.day).strftime("%m_%d_%Y"),
                "day": ts.day,
                "start_time": ts.start.strftime("%I:%M %p"),
                "end_time": ts.end.strftime("%I:%M %p")
            }
        )
    return standard_view('landing/course-details.html', {
        'course': course,
        'time_slots': final_result,
        'stripe_pk': settings.STRIPE_PUBLISHABLE_KEY,
    })(request)


def student_courses(request):
    me = AcademyUser.get_for(request.user)
    enrollments = Enrollment.objects.filter(student=me)
    print(enrollments)
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
    print(f"On login checking password: {request.POST['password']}, checking email: {request.POST['email']}")
    if user and user.is_authenticated and user.is_active:
        django_login(request, user)
        if user.groups.filter(name="Instructor").exists():
            if Instructor.objects.get(django_user=user).is_verified:
                return JsonResponse({'type': 'SUCCESS', 'message': 'Successfully logged in.', 'user': 2}, status=200)
            else:
                return JsonResponse({'type': 'ERROR', 'message': 'Your account is not verified yet', 'user': 2},
                                    status=200)
        else:
            return JsonResponse({'type': 'SUCCESS', 'message': 'Successfully logged in.', 'user': 1}, status=200)
    else:
        return JsonResponse({'type': 'ERROR', 'message': 'Incorrect username or password.'}, status=400)


def register(request):
    try:
        form = RegistrationForm(request.POST)
        student = form.save(commit=False)
        user = User.objects.create_user(username=request.POST['email'], email=request.POST['email'],
                                        password=request.POST['password'])
        user.is_active = False
        student.django_user = user
        user.save()
        student_group = Group.objects.get(name='Student')
        student_group.user_set.add(user)
        user.save()
        student.save()
        form.save_m2m()
    except:
        response = {
            "type": "ERROR",
            "message": "Couldn't able to create a account. Make sure the email is not registered already."
        }
        return JsonResponse(response, status=400)
    try:
        current_site = get_current_site(request)
        print(f"Current site: {current_site}")
        mail_subject = 'Activate your CMS Online Academy account.'
        token = account_activation_token.make_token(user)
        print(f"Token: {token}")
        message = render_to_string('acc_active_email.html', {
            'user': student.student_first_name + ' ' + student.student_last_name,
            # Add full name property in students model
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': token,
        })
        print(f"Message: {message}")
        email_from = settings.EMAIL_HOST_USER
        to_email = [request.POST['email']]
        send_mail(mail_subject, message, email_from, to_email)
    except:
        response = {
            "type": "ERROR",
            "message": "Couldn't able to send account confirmation mail"
        }
        return JsonResponse(response, status=400)
    response = {
        "type": "SUCCESS",
        "message": "Please confirm your email address to complete the registration"
    }
    return JsonResponse(response, status=200)


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        if user.groups.filter(name="Student").exists():
            django_login(request, user)
            print(f"User active status: {user.is_active}")
            print(f"User has usable password: {user.has_usable_password()}")
            return HttpResponseRedirect(reverse('student'))
        if user.groups.filter(name="Instructor").exists():
            if Instructor.objects.get(django_user=user).is_verified:
                return HttpResponseRedirect(reverse('instructor'))
            else:
                return HttpResponse('Please wait until your account get verified!')
    else:
        return HttpResponse('Activation link is invalid!')


def logout(request):
    django_logout(request)
    return HttpResponseRedirect(reverse('index'))


def email_query(request):
    email, name, query = request.POST['email'], request.POST['name'], request.POST['query']
    try:
        validate_email(email)
    except ValidationError:
        return HttpResponseRedirect(reverse('index'))

    message = render_to_string('query_email.html', {
        'name': name,
        'email': email,
        'message': query,
    })
    mail_subject = 'Query from ' + name
    email_from = settings.EMAIL_HOST_USER
    to_email = [settings.ORG_EMAIL]
    try:
        send_mail(mail_subject, message, email_from, to_email)
        response = {
            "type": "SUCCESS",
            "message": "Your query sent successfully. Please wait for reply."
        }
        return JsonResponse(response, status=200)
    except:
        response = {
            "type": "ERROR",
            "message": "Couldn't send query right now try again later"
        }
        return JsonResponse(response, status=400)


def checkout(request):
    form = PurchaseForm(request.POST)
    if form.is_valid():
        start_time, end_time = form.cleaned_data["time"].split(",")
        date_time = datetime.strptime(f'{form.cleaned_data["date"]} {start_time}', '%m/%d/%Y %I:%M %p')
        purchase = Purchase(
            course=Course.objects.get(pk=form.cleaned_data["course"]),
            course_datetime=date_time,
            student=AcademyUser.get_for(request.user),
            batch=form.cleaned_data["batch"]
        )
        enrollment = Enrollment(
            student=purchase.student,
            course=purchase.course,
            days=purchase.batch,
            start_time=datetime.strptime(start_time, '%I:%M %p').time(),
            end_time=datetime.strptime(end_time, '%I:%M %p').time(),
        )
        enrollment.save()
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'unit_amount': purchase.course.price_usd * 100,
                            'product_data': {
                                'name': purchase.course.name,
                            },
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=settings.STRIPE_DOMAIN + reverse('index'),  # TODO: Success
                cancel_url=settings.STRIPE_DOMAIN + reverse('index'),
                api_key=settings.STRIPE_API_KEY
            )
        except Exception as e:
            raise e
            return HttpResponse(str(e), status=403)

        purchase.stripe_id = checkout_session.stripe_id
        purchase.save()
        return HttpResponse(json.dumps({'id': checkout_session.id}))
    else:
        return HttpResponse("Not valid data", status=403)


@csrf_exempt
def checkout_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_ENDPOINT_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        purchase = Purchase.objects.get(stripe_id=session.id)
        purchase.confirmed = True
        purchase.save()

        print(session)

    # Passed signature verification
    return HttpResponse(status=200)


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    """
    Handles password reset tokens
    When a token is created, an e-mail needs to be sent to the user
    :param sender: View Class that sent the signal
    :param instance: View Instance that sent the signal
    :param reset_password_token: Token Model Object
    :param args:
    :param kwargs:
    :return:
    """
    # send an e-mail to the user
    context = {
        'current_user': reset_password_token.user,
        'username': reset_password_token.user.username,
        'email': reset_password_token.user.email,
        # 'reset_password_url': "{}?token={}".format(
        #     instance.request.build_absolute_uri(reverse('password_reset:reset-password-confirm')),
        #     reset_password_token.key)
        'reset_password_url': reset_password_token.key
    }

    # render email text
    email_html_message = render_to_string('password_reset/user_reset_password.html', context)
    email_plaintext_message = render_to_string('password_reset/user_reset_password.txt', context)

    msg = EmailMultiAlternatives(
        # title:
        "Password Reset for {title}".format(title=settings.PROJECT_TITLE),
        # message:
        email_plaintext_message,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [reset_password_token.user.email]
    )
    msg.attach_alternative(email_html_message, "text/html")
    msg.send()


@receiver(pre_password_reset)
def before_password_reset(sender, user, *args, **kwargs):
    print(f'Check before password reset, user active status: {user.is_active}')


@receiver(post_password_reset)
def after_password_reset(sender, user, *args, **kwargs):
    print(f'Check after password reset, user active status: {user.is_active}')


class CalendarView(generic.ListView):
    model = Event
    template_name = 'student/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # use today's date for the calendar
        d = get_date(self.request.GET.get('month', None))
        context['prev_month'] = prev_month(d)
        context['next_month'] = next_month(d)
        # Instantiate our calendar class with today's year and date
        cal = Calendar(d.year, d.month, self.kwargs["user_id"])

        # Call the formatmonth method, which returns our calendar as a table
        html_cal = cal.formatmonth(withyear=True)
        context['calendar'] = mark_safe(html_cal)
        return context


class InstructorCalendarView(generic.ListView):
    model = Event
    template_name = 'instructor/instructor_calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # use today's date for the calendar
        d = get_date(self.request.GET.get('month', None))
        context['prev_month'] = prev_month(d)
        context['next_month'] = next_month(d)
        student_id = self.kwargs["student_id"]
        student = Student.objects.get(pk=student_id)
        # Instantiate our calendar class with today's year and date
        cal = Calendar(d.year, d.month, student.django_user.id)
        # Call the formatmonth method, which returns our calendar as a table
        html_cal = cal.formatmonth(withyear=True)
        context['calendar'] = mark_safe(html_cal)
        context['student_id'] = student_id
        context['instructor_id'] = self.kwargs["instructor_id"]
        return context


def get_date(req_day):
    if req_day:
        year, month = (int(x) for x in req_day.split('-'))
        return date(year, month, day=1)
    return datetime.today()


def prev_month(d):
    first = d.replace(day=1)
    prev_month = first - timedelta(days=1)
    month = 'month=' + str(prev_month.year) + '-' + str(prev_month.month)
    return month


def next_month(d):
    days_in_month = calendar.monthrange(d.year, d.month)[1]
    last = d.replace(day=days_in_month)
    next_month = last + timedelta(days=1)
    month = 'month=' + str(next_month.year) + '-' + str(next_month.month)
    return month


def update_event(request, event_id=None):
    instance = Event()
    if event_id:
        instance = get_object_or_404(Event, pk=event_id)
    else:
        instance = Event()
    form = EventForm(request.POST or None, instance=instance, initial={'user': request.user})
    if request.POST and form.is_valid():
        event = form.save(commit=False)
        event.user = request.user
        event.save()
        return HttpResponseRedirect(reverse('student-schedule', kwargs={'user_id': request.user.id}))
    return render(request, 'update_event.html', {'form': form})


# Instructor views #
@csrf_exempt
def instructor_reg_form(request):
    speciality_level = SpecialityLevel.objects.all()
    speciality = Speciality.objects.all()
    available_days = AvailableDays.objects.all().filter(available=True).order_by('day')
    available_time = AvailableTimes.objects.all().filter(available=True).order_by('start')
    return render(request, 'landing/reg-form.html', {
        "speciality_level": speciality_level,
        "speciality": speciality,
        "available_days": available_days,
        "available_time": available_time
    })


@csrf_exempt
def instructor_register(request):
    data = json.loads(request.body)
    instructor = Instructor.create(data)
    try:
        current_site = get_current_site(request)
        print(f"Current site: {current_site}")
        mail_subject = 'Activate your CMS Online Academy account.'
        token = account_activation_token.make_token(instructor.django_user)
        print(f"Token: {token}")
        message = render_to_string('acc_active_email.html', {
            'user': instructor,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(instructor.django_user.pk)),
            'token': token,
        })
        print(f"Message: {message}")
        email_from = settings.EMAIL_HOST_USER
        to_email = [request.POST['email']]
        send_mail(mail_subject, message, email_from, to_email)
    except:
        response = {
            "type": "ERROR",
            "message": "Couldn't able to send account confirmation mail"
        }
        return JsonResponse(response, status=400)
    response = {
        "type": "SUCCESS",
        "message": "Please confirm your email address to complete the registration"
    }
    return JsonResponse(response, status=200)


def instructor_base(request):
    me = AcademyUser.get_for(request.user)
    return render(request, 'instructor/instructor-base.html', {"instructor_id": me.pk})


@csrf_exempt
def instructor_skill_update(request, instructor_id):
    data = json.loads(request.body)
    instructor = Instructor.objects.get(pk=instructor_id)
    try:
        InstructorSpeciality.objects.filter(instructor=instructor).delete()
        for sp in data["speciality"]:
            sp_pk = sp[0]  # speciality pk
            spl_pk = sp[1]  # speciality_level pk
            speciality = Speciality.objects.get(pk=sp_pk)
            speciality_level = SpecialityLevel.objects.get(pk=spl_pk)
            instructor_speciality = InstructorSpeciality(instructor=instructor, speciality=speciality,
                                                         speciality_level=speciality_level)
            instructor_speciality.save()
    except:
        return JsonResponse({"type": "ERROR", "message": "Couldn't able to update skill"}, status=403)
    return JsonResponse({"type": "SUCCESS", "message": "Skills successfully updated"}, status=200)


def instructor_classes(request, instructor_id):
    classes = StudentInstructor.objects.filter(instructor=instructor_id)
    return render(request, 'instructor/classes.html', {"classes": classes, "instructor_id": instructor_id})


def instructor_material(request, instructor_id):
    material = CourseMaterial.objects.filter(uploader=instructor_id)
    return render(request, 'instructor/material.html', {"material": material, "instructor_id": instructor_id})


def instructor_student_assignment(request, instructor_id):
    classes = StudentInstructor.objects.filter(instructor=instructor_id)
    return render(request, 'instructor/test_assignment_dashboard.html',
                  {"classes": classes, "instructor_id": instructor_id})


def update_instructor(request, instructor_id=None):
    instance = Instructor()
    if instructor_id:
        instance = get_object_or_404(Instructor, pk=instructor_id)
    else:
        instance = Instructor()
    form = InstructorForm(request.POST or None, instance=instance)
    if request.POST and form.is_valid():
        instructor = form.save(commit=False)
        instructor.save()
        return HttpResponseRedirect(reverse('instructor'))
    instructor_specialities = InstructorSpeciality.objects.filter(instructor=instance)
    speciality_level = SpecialityLevel.objects.all()
    speciality = Speciality.objects.all()
    result = []
    for in_sp in instructor_specialities:
        result.append([in_sp.speciality.id, in_sp.speciality_level.id])
    return render(request, 'instructor/profile.html',
                  {'form': form, 'instructor_specialities': result,
                   "speciality_level": speciality_level,
                   "speciality": speciality,
                   "instructor_id": instructor_id
                   })


def instructor_student_works(request, instructor_id, enrollment_id, exam_id=None, exam_grade_id=None, project_id=None):
    student_instructor = StudentInstructor.objects.get(enrollment=enrollment_id, instructor=instructor_id)
    # Exam form
    if project_id:
        exam_instance = get_object_or_404(Exam, pk=exam_id)
    else:
        exam_instance = Exam()
    exam_form = ExamForm(request.POST or None, instance=exam_instance)
    if request.POST and exam_form.is_valid():
        exam = exam_form.save(commit=False)
        exam.course = student_instructor.enrollment.course
        exam.save()
        return HttpResponseRedirect('')
    # Exam grade form
    if exam_grade_id:
        exam_grade_instance = get_object_or_404(ExamGrade, pk=exam_grade_id)
    else:
        exam_grade_instance = ExamGrade()
    exam_grade_form = ExamGradeForm(student_instructor.enrollment.course.pk, request.POST or None,
                                    instance=exam_grade_instance)
    if request.POST and exam_grade_form.is_valid():
        exam_grade = exam_grade_form.save(commit=False)
        exam_grade.student = student_instructor.enrollment.student
        if ExamGrade.objects.filter(exam=exam_grade.exam).exists():
            new_exam_grade = ExamGrade.objects.get(exam=exam_grade.exam)
            new_exam_grade.grade = exam_grade.grade
            new_exam_grade.save()
        else:
            exam_grade.save()
        return HttpResponseRedirect('')
    # Project form
    if project_id:
        project_instance = get_object_or_404(Project, pk=project_id)
    else:
        project_instance = Project()
    project_form = ProjectForm(request.POST or None, instance=project_instance)
    if request.POST and project_form.is_valid():
        project = project_form.save(commit=False)
        project.course = student_instructor.enrollment.course
        project.save()
        return HttpResponseRedirect('')
    return render(request, 'instructor/student_test_assignment.html',
                  {"student_instructor": student_instructor, "instructor_id": instructor_id,
                   "project_form": project_form, "exam_form": exam_form, "exam_grade_form": exam_grade_form})
