import json
import stripe
from django.db import IntegrityError
from django.contrib.auth import login as django_login, logout as django_logout, authenticate
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import loader
from django.urls import reverse
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.csrf import csrf_exempt

from django.conf import settings
from api.models import AcademyUser, Category, Product, Order, Purchase, ServiceProvider, Customer, OrderStatus
from academy_backend import settings
from api.forms import RegistrationForm, PurchaseForm, ServiceProviderForm

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
from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
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
    trending = Product.objects.order_by('-purchase')[:2]
    fresh = Product.objects.order_by('-id')[:3]

    return standard_view('landing/index.html', {
        'trending': trending,
        'fresh': fresh,
    })(request)


def product_category(request):
    categories = Category.objects.all()
    return standard_view('landing/product-category.html', {
        'categories': categories,
    })(request)


def product_offered(request, category_id):
    category = Category.objects.get(id=category_id)

    return standard_view('landing/product-offered.html', {
        'category': category,
    })(request)


def product_details(request, course_id):
    product = Product.objects.get(id=course_id)
    try:
        mode = request.GET["mode"]
    except MultiValueDictKeyError:
        mode = 1
    return standard_view('landing/product-details.html', {
        'product': product,
        'stripe_pk': settings.STRIPE_PUBLISHABLE_KEY,
        'mode': mode
    })(request)


def customer_orders(request):
    me = AcademyUser.get_for(request.user)
    orders = Order.objects.filter(student=me)
    # deleting unconfirmed purchases
    for ord in orders:
        if not ord.purchase.confirmed:
            purchase = Purchase.objects.get(pk=ord.purchase.pk)
            purchase.delete()
    return standard_view('customer/products.html', {
        'orders': orders
    })(request)


def customer_profile(request):
    me = AcademyUser.get_for(request.user)
    if request.method == 'POST':
        form = RegistrationForm(request.POST, instance=me)
        if form.is_valid():
            user = form.save()
            user.save()
            return JsonResponse({'type': 'SUCCESS', 'message': 'Successfully updated.'}, status=200)
        else:
            return JsonResponse({'type': 'ERROR', 'message': 'Update failed!, No valid data.'}, status=400)

    return standard_view('customer/profile.html')(request)


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


def checkout(request):
    form = PurchaseForm(request.POST)
    if form.is_valid():
        start_time, end_time = form.cleaned_data["time"].split(",")
        date_time = datetime.strptime(f'{form.cleaned_data["date"]} {start_time}', '%m/%d/%Y %I:%M %p')
        purchase = Purchase(
            product=Product.objects.get(pk=form.cleaned_data["product"]),
            datetime=date_time,
            customer=AcademyUser.get_for(request.user)
        )
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'unit_amount': purchase.product.total_price_usd * 100,
                            'product_data': {
                                'name': purchase.product.name,
                            },
                        },
                        'quantity': 1,
                    }
                ],
                mode='payment',
                success_url=settings.STRIPE_DOMAIN + reverse('index'),  # TODO: Success
                cancel_url=settings.STRIPE_DOMAIN + reverse('index'),
                api_key=settings.STRIPE_API_KEY,
                metadata={"order_status": OrderStatus.pending}
            )
        except Exception as e:
            return HttpResponse(str(e), status=403)

        purchase.stripe_id = checkout_session.stripe_id
        try:
            purchase.save()
        except IntegrityError:
            return JsonResponse(
                {"type": "ERROR", "message": "Sorry! You cannot order. Check if you have already ordered this item."},
                status=400)
        order = Order(
            customer=purchase.customer,
            product=purchase.product,
            purchase=purchase,
            order_status=OrderStatus.pending
        )
        order.save()
        return HttpResponse(json.dumps({'id': checkout_session.id, 'order_status': OrderStatus.pending}))
    else:
        return HttpResponse("Not valid data", status=403)


@csrf_exempt
def checkout_webhook(request):
    print("----------Starting checkout webhook-------------")
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
        order_status = int(event.data.object.metadata["order_status"])
        print(f"Data: {event.data.object.metadata}")
        if order_status == OrderStatus.pending:
            session = event['data']['object']
            purchase = Purchase.objects.get(stripe_id=session.id)
            purchase.confirmed = True
            purchase.save()
            order = Order.objects.get(purchase=purchase)
            order.order_status = OrderStatus.accepted
            order.save()
            print(session)
    # Passed signature verification
    return HttpResponse(status=200)


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):

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


# Service provider views #
@csrf_exempt
def service_provider_reg_form(request):
    return render(request, 'landing/reg-form.html', {})


@csrf_exempt
def service_provider_register(request):
    data = json.loads(request.body)
    try:
        service_provider = ServiceProvider.create(data)
    except:
        response = {
            "type": "ERROR",
            "message": "Unable to create an account. Make sure that your email is not registered with another account."
        }
        return JsonResponse(response, status=400)
    try:
        current_site = get_current_site(request)
        print(f"Current site: {current_site}")
        mail_subject = 'Activate your CMS Online Academy account.'
        token = account_activation_token.make_token(service_provider.django_user)
        print(f"Token: {token}")
        message = render_to_string('acc_active_email.html', {
            'user': service_provider,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(service_provider.django_user.pk)),
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


def service_provider_base(request):
    me = AcademyUser.get_for(request.user)
    return render(request, 'service_provider/service_provider-base.html', {"service_provider_id": me.pk})


def update_service_provider(request, service_provider_id=None):
    service_provider = ServiceProvider()
    if service_provider_id:
        service_provider = get_object_or_404(ServiceProvider, pk=service_provider_id)
    else:
        service_provider = ServiceProvider()
    form = ServiceProviderForm(request.POST or None, instance=service_provider)
    if request.POST:
        if form.is_valid():
            service_provider = form.save(commit=False)
            service_provider.save()
            return JsonResponse({'type': 'SUCCESS', 'message': 'Successfully updated.'}, status=200)
        else:
            return JsonResponse({'type': 'ERROR', 'message': 'Update failed!, No valid data.'}, status=400)
    return standard_view('service_provider/profile.html',
                         {'form': form,
                          "service_provider_id": service_provider_id
                          })(request)
