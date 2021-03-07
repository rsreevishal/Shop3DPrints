from api.models import Order
from api.forms import RegistrationForm
from .helpers import *


def customer_products(request):
    me = AcademyUser.get_for(request.user)
    products = Product.objects.filter(customer=me)
    return standard_view('customer/products.html', {
        'products': products
    })(request)


def customer_orders(request):
    me = AcademyUser.get_for(request.user)
    prod_ids = [products.pk for products in Product.objects.filter(customer=me)]
    orders = Order.objects.filter(product__in=prod_ids)
    return standard_view('customer/orders.html', {
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
