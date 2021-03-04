import json
import uuid
import stripe
from django.db import IntegrityError
from django.contrib.auth import login as django_login, logout as django_logout, authenticate
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import loader
from django.urls import reverse
from django.utils import timezone
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.csrf import csrf_exempt

from django.conf import settings
from api.models import AcademyUser, Category, Product, Order, Purchase, ServiceProvider, Customer, OrderStatus, \
    CategoryMaterial, Density, LayerHeight
from academy_backend import settings
from api.forms import RegistrationForm, PurchaseForm, ServiceProviderForm

from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.core.mail import send_mail, EmailMessage
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver
from django_rest_passwordreset.signals import reset_password_token_created
from datetime import datetime
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import Group
from weasyprint import HTML


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


def product_category(request):
    categories = Category.objects.all()
    return standard_view('landing/product-category.html', {
        'categories': categories,
    })(request)


def product_offered(request, category_id):
    category = Category.objects.get(id=category_id)
    category_material = CategoryMaterial.objects.filter(category=category)
    density_list = Density.objects.all()
    layer_height_list = LayerHeight.objects.all()
    return standard_view('landing/product-offered.html', {
        'category': category,
        'category_material': category_material,
        'density_list': density_list,
        'layer_height_list': layer_height_list
    })(request)


def product_details(request, product_id):
    product = Product.objects.get(pk=product_id)
    category_material = CategoryMaterial.objects.filter(category=product.category)
    density_list = Density.objects.all()
    layer_height_list = LayerHeight.objects.all()
    orders = Order.objects.filter(product=product)
    service_provider = ServiceProvider.objects.all()
    return standard_view('customer/product.html', {
        'product': product,
        'stripe_pk': settings.STRIPE_PUBLISHABLE_KEY,
        'category_material': category_material,
        'density_list': density_list,
        'layer_height_list': layer_height_list,
        'orders': orders,
        'service_provider': service_provider
    })(request)


def customer_products(request):
    me = AcademyUser.get_for(request.user)
    products = Product.objects.filter(customer=me)
    return standard_view('customer/products.html', {
        'products': products
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
    try:
        order = Order.objects.get(pk=int(request.POST.get("order_id")))
        purchase = Purchase(
            order=order,
            datetime=timezone.now()
        )
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'inr',
                            'unit_amount': int(purchase.order.total_cost * 100),
                            'product_data': {
                                'name': purchase.order.product.name,
                            },
                        },
                        'quantity': 1,
                    }
                ],
                mode='payment',
                success_url=settings.STRIPE_DOMAIN + reverse('customer-products'),  # TODO: Success
                cancel_url=settings.STRIPE_DOMAIN + reverse('customer-products'),
                api_key=settings.STRIPE_API_KEY
            )
        except Exception as e:
            print(f"Couldn't checkout: {e}")
            return HttpResponse(str(e), status=403)

        purchase.stripe_id = checkout_session.stripe_id
        try:
            purchase.save()
        except IntegrityError:
            return JsonResponse(
                {"type": "ERROR", "message": "Sorry! You cannot order. Check if you have already ordered this item."},
                status=400)
        return HttpResponse(json.dumps({'id': checkout_session.id, 'order_status': OrderStatus.pending}))
    except Exception as e:
        print(f"Couldn't checkout: {e}")
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
        session = event['data']['object']
        purchase = Purchase.objects.get(stripe_id=session.id)
        purchase.confirmed = True
        purchase.save()
        order = purchase.order
        order.order_status = OrderStatus.payed
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


def service_provider_base(request):
    me = AcademyUser.get_for(request.user)
    return render(request, 'service_provider/service_provider-base.html', {"service_provider_id": me.pk})


def update_service_provider(request):
    service_provider_id = AcademyUser.get_for(request.user).pk
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
    return standard_view('service_provider/profile.html', {'form': form, "service_provider_id": service_provider_id}) \
        (request)


def post_get(request, attr):
    return request.POST.get(attr)


def add_to_cart(request):
    if request.POST and request.FILES['stl_file']:
        product = Product.parse_request(request)
        product.customer = Customer.objects.get(pk=int(request.POST.get('customer_id')))
        category = Category.objects.get(pk=int(request.POST.get('category')))
        product.category = category
        stl_file = request.FILES['stl_file']
        product.stl_file = stl_file
        product.save()
    return HttpResponseRedirect(reverse('customer-products'))


def update_cart(request, product_id: int):
    if request.POST:
        old_product = Product.objects.get(pk=product_id)
        new_product = Product.parse_request(request)
        old_product.name = new_product.name
        old_product.description = new_product.description
        old_product.material = new_product.material
        old_product.density = new_product.density
        old_product.layer_height = new_product.layer_height
        try:
            stl_file = request.FILES['stl_file']
            old_product.stl_file = stl_file
        except Exception as e:
            pass
        old_product.save()
    return HttpResponseRedirect(reverse('customer-products'))


def service_provider_orders(request):
    me = AcademyUser.get_for(request.user)
    orders = Order.objects.filter(service_provider=me)
    return standard_view('service_provider/orders.html', {"orders": orders})(request)


def add_order(request):
    if request.POST:
        print(request.POST)
        try:
            product = Product.objects.get(pk=int(request.POST.get('product')))
            quantity = int(request.POST.get('quantity'))
            service_provider = ServiceProvider.objects.get(pk=int(request.POST.get('service_provider')))
            order = Order(product=product, quantity=quantity, service_provider=service_provider,
                          ordered_on=timezone.now(), order_status=OrderStatus.pending)
            order.save()
            return JsonResponse({"type": "SUCCESS", "message": "Your order is placed successfully"}, status=200)
        except Exception as e:
            return JsonResponse({"type": "ERROR", "message": "Your order is failed. Try again"}, status=200)
    return JsonResponse({"type": "ERROR", "message": "Your order is failed. Try again"}, status=200)


def service_provider_order_details(request, order_id: int = None):
    try:
        order = Order.objects.get(pk=order_id)
        product = order.product
        total_cost = (product.material.cost + product.density.cost + product.layer_height.cost) * order.quantity
        return standard_view('service_provider/order_details.html', {"order": order, "total_cost": total_cost})(request)
    except Exception as e:
        print(e)
        return HttpResponseRedirect(reverse('service_provider_orders'))


def html_to_pdf_view(order, file_name):
    try:
        html_string = render_to_string('service_provider/invoice_template.html',
                                       {"order": order, "file_name": file_name})
        html = HTML(string=html_string)
        html.write_pdf(target=f'media/invoice/{file_name}')
        return True
    except Exception as e:
        print(f"Error occured in pdf: {e}")
        return False


def generate_quote(request, order_id: int = None):
    try:
        if request.POST:
            order = Order.objects.get(pk=order_id)
            if request.POST.get('additional_value'):
                order.additional_value = request.POST.get('additional_value')
            if request.POST.get('additional_cost'):
                order.additional_cost = float(request.POST.get('additional_cost'))
            if request.POST.get('total_cost'):
                order.total_cost = float(request.POST.get('total_cost'))
            if request.POST.get('comments'):
                order.comments = request.POST.get('comments')
            file_name = f'{str(uuid.uuid4())}.pdf'
            if html_to_pdf_view(order, file_name):
                order.invoice_generated = True
                order.invoice_file_name = file_name
                order.order_status = OrderStatus.quoted
            order.save()
            email = EmailMessage(
                'Your order was received', f'Hello {order.product.customer}. We processed your invoice',
                settings.DEFAULT_FROM_EMAIL, [order.product.customer.django_user.email])
            email.attach_file(f'media/invoice/{file_name}')
            email.send()
            return JsonResponse({"type": "SUCCESS",
                                 "message": "Successfully generated quote and sent to customer email."}, status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"type": "ERROR", "message": "Failed to generate quote."}, status=200)


def service_provider_update_status(request, order_id: int = None):
    try:
        order = Order.objects.get(pk=order_id)
        order.order_status = int(request.POST.get('status_id'))
        if 'comments' in request.POST:
            order.comments = request.POST.get('comments')
        order.save()
        try:
            message = render_to_string('status_update_template.html', {
                'order': order,
                'status_name': ["Completed", "Cancelled", "Quoted", "Pending", "Shipped", "Payed"][order.order_status],
                'project_title': settings.PROJECT_TITLE
            })
            print(f"Message: {message}")
            email_from = settings.EMAIL_HOST_USER
            to_email = [order.product.customer.django_user.email]
            send_mail(f"{settings.PROJECT_TITLE} status update", message, email_from, to_email)
        except Exception as e:
            print(e)
        return JsonResponse({"type": "SUCCESS", "message": "Order status is updated successfully."}, status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"type": "ERROR", "message": "Order status update failed."}, status=200)
