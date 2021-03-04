from django.urls import path, include
from api.views import *

urlpatterns = [
    path('', index, name='index'),
    path('about-us', standard_view('landing/about-us.html'), name='about-us'),
    path('faq', standard_view('landing/faq.html'), name='faq'),
    path('product/category', product_category, name='product-category'),
    path(r'products-offered/<str:category_id>', product_offered, name='products-offered'),
    path('product-details/<int:product_id>', product_details, name='product-details'),
    path('customer', redirect_view('customer-products'), name='customer'),
    path('customer/products', customer_products, name='customer-products'),
    path('customer/profile', customer_profile, name='customer-profile'),
    path('service_provider', service_provider_base, name='service_provider'),
    path('service_provider/orders', service_provider_orders, name='service_provider_orders'),
    path('service_provider/orders/<int:order_id>', service_provider_order_details, name='service_provider_order_details'),
    path('api/service_provider/profile/edit/', update_service_provider,
         name='service_provider-profile-edit'),
    path('api/login', login, name='login'),
    path('api/register', register, name='register'),
    path('activate/<uidb64>/<token>', activate, name='activate'),
    path('api/logout', logout, name='logout'),
    path('api/checkout', checkout, name='checkout'),
    path('api/checkout-webhook', checkout_webhook, name='checkout-webhook'),
    path('api/query', email_query, name='query'),
    path('api/password_reset/', include('django_rest_passwordreset.urls'), name='password_reset'),
    path('api/customer/cart', add_to_cart, name='add_to_cart'),
    path('api/customer/cart/<int:product_id>', update_cart, name='update_cart'),
    path('api/customer/order/', add_order, name="add_order"),
    path('api/service_provider/quote/order/<int:order_id>', generate_quote, name="quote_order"),
    path('api/service_provider/order/<int:order_id>/status', service_provider_update_status,
         name='service_provider_update_status')
]
