from django.contrib import admin

from api.models import *

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(ServiceProvider)
admin.site.register(Purchase)
admin.site.register(Customer)
admin.site.register(Subcategory)

