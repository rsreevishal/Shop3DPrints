from django.utils import timezone
from api.models import Order, Purchase, ServiceProvider
from api.forms import ServiceProviderForm
from datetime import timedelta
from django.shortcuts import render, get_object_or_404
from .whatsapp import WhatsAppMessage
from .helpers import *


def sunday_to_today_revenue(date):
    tmp = date
    revenues = [get_total_revenue(tmp)]
    while tmp.weekday() != 6:
        tmp = tmp - timedelta(days=1)
        revenues.append(get_total_revenue(tmp))
    return revenues


def get_total_revenue(date):
    revenue = 0
    for row in Purchase.objects.filter(datetime__date=date):
        revenue += row.order.total_cost
    return revenue


def sunday_to_today_orders(date):
    tmp = date
    orders = [get_total_orders(tmp)]
    while tmp.weekday() != 6:
        tmp = tmp - timedelta(days=1)
        orders.append(get_total_orders(tmp))
    return orders


def get_total_orders(date):
    return len(Order.objects.filter(ordered_on__date=date))


def service_provider_base(request):
    me = AcademyUser.get_for(request.user)
    total_revenue = 0
    for row in Purchase.objects.all():
        total_revenue += row.order.total_cost
    total_orders = len(Order.objects.all())
    today_orders = get_total_orders(timezone.now().date())
    today_revenue = get_total_revenue(timezone.now().date())
    week_revenue = sunday_to_today_revenue(timezone.now().date())
    week_orders = sunday_to_today_orders(timezone.now().date())
    return render(request, 'service_provider/service_provider-base.html',
                  {"service_provider_id": me.pk, "total_revenue": total_revenue, "total_orders": total_orders,
                   "today_orders": today_orders, "today_revenue": today_revenue, "week_revenue": week_revenue,
                   "week_orders": week_orders})


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


def service_provider_orders(request):
    me = AcademyUser.get_for(request.user)
    orders = Order.objects.filter(service_provider=me)
    return standard_view('service_provider/orders.html', {"orders": orders})(request)


def service_provider_order_details(request, order_id: int = None):
    try:
        order = Order.objects.get(pk=order_id)
        product = order.product
        total_cost = (product.material.cost + product.density.cost + product.layer_height.cost) * order.quantity
        return standard_view('service_provider/order_details.html', {"order": order, "total_cost": total_cost})(request)
    except Exception as e:
        print(e)
        return HttpResponseRedirect(reverse('service_provider_orders'))


def service_provider_update_status(request, order_id: int = None):
    try:
        order = Order.objects.get(pk=order_id)
        order.order_status = int(request.POST.get('status_id'))
        if 'comments' in request.POST:
            order.comments = request.POST.get('comments')
        order.save()
        status_names = ["Completed", "Cancelled", "Quoted", "Pending", "Shipped", "Payed"]
        try:
            message = render_to_string('status_update_template.html', {
                'order': order,
                'status_name': status_names[order.order_status],
                'project_title': settings.PROJECT_TITLE
            })
            print(f"Message: {message}")
            email_from = settings.EMAIL_HOST_USER
            to_email = [order.product.customer.django_user.email]
            send_mail(f"{settings.PROJECT_TITLE} status update", message, email_from, to_email)
        except Exception as e:
            print(e)
        try:
            wapp = WhatsAppMessage()
            wapp.send_message(f'whatsapp:+{order.product.customer.country}{order.product.customer.phone_number}',
                              f'Your order *{order.product.name}* status is updated to: *{status_names[order.order_status]}* by {order.service_provider}')
        except Exception as e:
            print(e)
        return JsonResponse({"type": "SUCCESS", "message": "Order status is updated successfully."}, status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"type": "ERROR", "message": "Order status update failed."}, status=200)
