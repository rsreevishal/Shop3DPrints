import json
import stripe

from django.contrib.auth import login as django_login, logout as django_logout, authenticate
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import loader
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from django.conf import settings
from api.models import AcademyUser, Category, Course, Enrollment, Purchase
from academy_backend import settings
from api.forms import RegistrationForm, PurchaseForm

from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


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
        'stripe_pk': settings.STRIPE_PUBLISHABLE_KEY,
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
        return JsonResponse({'type': 'SUCCESS', 'message': 'Successfully logged in.'})
    else:
        return JsonResponse({'type': 'ERROR', 'message': 'Incorrect username or password.'})


def register(request):
    try:
        form = RegistrationForm(request.POST)
        student = form.save(commit=False)
        user = User.objects.create_user(username=request.POST['email'], password=request.POST['password'])
        user.is_active = False
        student.django_user = user
        user.save()
        student.save()
        form.save_m2m()
    except:
        response = {
            "type": "ERROR",
            "message": "Couldn't able to create a account. Make sure the email is not registered already."
        }
        return JsonResponse(response)
    try:
        current_site = get_current_site(request)
        print(f"Current site: {current_site}")
        mail_subject = 'Activate your CMS Online Academy account.'
        token = account_activation_token.make_token(user)
        print(f"Token: {token}")
        message = render_to_string('acc_active_email.html', {
            'user': student.student_first_name + ' ' + student.student_last_name,       # Add full name property in students model
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
        return JsonResponse(response)
    response = {
        "type": "ERROR",
        "message": "Please confirm your email address to complete the registration"
    }
    return JsonResponse(response)


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
    send_mail(mail_subject, message, email_from, to_email)
    return HttpResponseRedirect(reverse('index'))


def checkout(request):
    form = PurchaseForm(request.POST)
    purchase = form.save(commit=False)

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
    purchase.student = AcademyUser.get_for(request.user)

    purchase.save()
    form.save_m2m()

    return HttpResponse(json.dumps({'id': checkout_session.id}))


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
