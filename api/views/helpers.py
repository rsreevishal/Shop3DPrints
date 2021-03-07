from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import loader
from api.models import AcademyUser, Category, Product
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.conf import settings
from academy_backend import settings
from django.template.loader import render_to_string


# Helper functions
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
    trending = Product.objects.order_by('-order')[:2]
    fresh = Product.objects.order_by('-id')[:3]

    return standard_view('landing/index.html', {
        'trending': trending,
        'fresh': fresh,
    })(request)


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
            "message": "Your query has been sent successfully. Kindly wait for the reply"
        }
        return JsonResponse(response, status=200)
    except:
        response = {
            "type": "ERROR",
            "message": "Couldn't send query right now try again later"
        }
        return JsonResponse(response, status=400)
