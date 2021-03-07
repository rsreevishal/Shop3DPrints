from django.contrib.auth import login as django_login, logout as django_logout, authenticate
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse

from django.conf import settings
from api.models import ServiceProvider
from academy_backend import settings
from api.forms import RegistrationForm
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from api.tokens import account_activation_token
from django.core.mail import send_mail
from django.contrib.auth.models import Group
from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver
from django_rest_passwordreset.signals import reset_password_token_created


def login(request):
    user: User = authenticate(username=request.POST['email'], password=request.POST['password'])
    if user and user.is_authenticated and user.is_active:
        django_login(request, user)
        if user.groups.filter(name="ServiceProvider").exists():
            if ServiceProvider.objects.get(django_user=user).is_verified:
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
        customer = form.save(commit=False)
        user = User.objects.create_user(username=request.POST['email'], email=request.POST['email'],
                                        password=request.POST['password'])
        user.is_active = False
        customer.django_user = user
        user.save()
        customer_group = Group.objects.get(name='Customer')
        customer_group.user_set.add(user)
        user.save()
        customer.save()
        form.save_m2m()
    except:
        response = {
            "type": "ERROR",
            "message": "Unable to create an account. Make sure that your email is not registered with another account."
        }
        return JsonResponse(response, status=400)
    try:
        current_site = get_current_site(request)
        print(f"Current site: {current_site}")
        mail_subject = 'Activate your Shop3DPrints account.'
        token = account_activation_token.make_token(user)
        print(f"Token: {token}")
        message = render_to_string('acc_active_email.html', {
            'user': customer.first_name + ' ' + customer.last_name,
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
        "message": "Registered successfully. Click on the activation link sent to your mail to activate your account."
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
        if user.groups.filter(name="Customer").exists():
            # django_login(request, user)
            print(f"User active status: {user.is_active}")
            print(f"User has usable password: {user.has_usable_password()}")
            return HttpResponseRedirect(reverse('index') + "?mode=2")
        if user.groups.filter(name="ServiceProvider").exists():
            if ServiceProvider.objects.get(django_user=user).is_verified:
                return HttpResponseRedirect(reverse('index') + "?mode=2")
            else:
                return HttpResponse('Please wait until your account get verified!')
    else:
        return HttpResponse('Activation link is invalid!')


def logout(request):
    django_logout(request)
    return HttpResponseRedirect(reverse('index'))


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    # send an e-mail to the user
    context = {
        'current_user': reset_password_token.user,
        'username': reset_password_token.user.username,
        'email': reset_password_token.user.email,
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
