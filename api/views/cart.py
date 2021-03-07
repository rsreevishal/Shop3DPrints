from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.utils import timezone
from api.models import Category, Product, Order, ServiceProvider, Customer, OrderStatus


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
            print(e)
            pass
        old_product.save()
    return HttpResponseRedirect(reverse('customer-products'))


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