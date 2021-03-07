from api.models import Order, ServiceProvider, CategoryMaterial, Density, LayerHeight
from .helpers import *


# Product views
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
