from django.contrib import admin
from .models import CustomUser, Category, Breed, Fish, Cart, Order, OrderItem, OTP, Review, Service, ContactInfo, LimitedOffer

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

@admin.register(LimitedOffer)
class LimitedOfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'discount_text', 'fish', 'start_time', 'end_time', 'is_active', 'show_on_homepage')
    list_filter = ('is_active', 'show_on_homepage', 'start_time', 'end_time')
    search_fields = ('title', 'description', 'discount_text')
    list_editable = ('is_active', 'show_on_homepage')
    date_hierarchy = 'start_time'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Offer Details', {
            'fields': ('title', 'description', 'discount_text')
        }),
        ('Visual Settings', {
            'fields': ('image', 'bg_color')
        }),
        ('Redirect Settings', {
            'fields': ('fish',),
            'description': 'Optional: Select a specific fish to redirect users when they click the banner. If not selected, users will be redirected to the fish list page.'
        }),
        ('Schedule', {
            'fields': ('start_time', 'end_time')
        }),
        ('Display Options', {
            'fields': ('is_active', 'show_on_homepage')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


