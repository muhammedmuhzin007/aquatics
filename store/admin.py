from django.contrib import admin
from .models import CustomUser, Category, Breed, Fish, Cart, Order, OrderItem, OTP, Review, Service, ContactInfo

admin.site.register(CustomUser)
admin.site.register(Category)
admin.site.register(Breed)
admin.site.register(Fish)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(OTP)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('order', 'user', 'rating', 'approved', 'created_at')
    list_filter = ('approved', 'rating', 'created_at')
    search_fields = ('user__username', 'order__order_number', 'comment')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'display_order', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description')
    list_editable = ('is_active', 'display_order')

@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = ('address_line1', 'city', 'phone_primary', 'email_support', 'updated_at')
    search_fields = ('address_line1', 'city', 'phone_primary', 'email_support')
    readonly_fields = ('created_at', 'updated_at')


