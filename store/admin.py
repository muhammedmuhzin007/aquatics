from django.contrib import admin
from .models import CustomUser, Category, Breed, Fish, Cart, Order, OrderItem, OTP

admin.site.register(CustomUser)
admin.site.register(Category)
admin.site.register(Breed)
admin.site.register(Fish)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(OTP)

