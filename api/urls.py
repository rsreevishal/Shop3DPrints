from django.urls import path, include
from api.views import *

urlpatterns = [
    path('', index, name='index'),
    path('about-us', standard_view('landing/about-us.html'), name='about-us'),
    path('faq', standard_view('landing/faq.html'), name='faq'),
    path('product/category', product_category, name='product-category'),
    path(r'products-offered/<str:category_id>', product_offered, name='products-offered'),
    path('product-details/<int:product_id>', product_details, name='product-details'),
    path('reg-form', service_provider_reg_form, name='reg-form'),
    path('customer', redirect_view('customer-products'), name='customer'),
    path('customer/products', customer_orders, name='customer-products'),
    path('customer/profile', customer_profile, name='customer-profile'),
    path('service_provider', service_provider_base, name='service_provider'),
    path('service_provider/<int:service_provider_id>/profile/edit/', update_service_provider,
         name='service_provider-profile-edit'),
    path('api/login', login, name='login'),
    path('api/register', register, name='register'),
    path('activate/<uidb64>/<token>', activate, name='activate'),
    path('api/logout', logout, name='logout'),
    path('api/checkout', checkout, name='checkout'),
    path('api/checkout-webhook', checkout_webhook, name='checkout-webhook'),
    path('api/query', email_query, name='query'),
    path('api/password_reset/', include('django_rest_passwordreset.urls'), name='password_reset'),
    path('api/service_provider_register', service_provider_register, name="service_provider_register"),
    path('api/customer/cart', add_to_cart, name='add_to_cart')
]
