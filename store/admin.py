import re

from django import forms
from django.contrib import admin
from .models import (
    CustomUser,
    Category,
    Breed,
    Fish,
    Cart,
    Order,
    OrderItem,
    OTP,
    Review,
    Service,
    ContactInfo,
    LimitedOffer,
    BlogPost,
    Coupon,
    ComboOffer,
    ComboItem,
    FishCategory,
    ComboCategory,
    AccessoryCategory,
    PlantCategory,
    Plant,
    ShippingChargeSetting,
    ShippingChargeByLocation,
)

admin.site.register(CustomUser)
admin.site.register(Breed)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(OTP)


class BaseCategoryAdmin(admin.ModelAdmin):
    section_title = 'Category Details'
    category_type = None

    list_display = ('name', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at',)

    def get_fieldsets(self, request, obj=None):
        return (
            (self.section_title, {
                'fields': ('name', 'description', 'image')
            }),
            ('Timestamps', {
                'fields': ('created_at',),
                'classes': ('collapse',),
            }),
        )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.category_type:
            return qs.filter(category_type=self.category_type)
        return qs

    def save_model(self, request, obj, form, change):
        if self.category_type:
            obj.category_type = self.category_type
        super().save_model(request, obj, form, change)


class TagListWidget(forms.Widget):
    """Render newline-delimited values as removable chips in admin forms."""
    template_name = 'admin/widgets/tag_list_widget.html'

    def _split_values(self, value):
        if not value:
            return []
        if isinstance(value, (list, tuple)):
            return [self._clean_item(item) for item in value if self._clean_item(item)]
        parts = re.split(r'[,\n]+', str(value))
        return [self._clean_item(part) for part in parts if self._clean_item(part)]

    @staticmethod
    def _clean_item(item):
        text = str(item or '').strip()
        return text or None

    def format_value(self, value):
        return self._split_values(value)

    def value_from_datadict(self, data, files, name):
        values = self._split_values(data.get(name, ''))
        seen = set()
        unique = []
        for value in values:
            key = value.lower()
            if key not in seen:
                seen.add(key)
                unique.append(value)
        return '\n'.join(unique)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        tokens = self._split_values(value)
        widget_ctx = context['widget']
        widget_ctx['tag_values'] = tokens
        widget_ctx['joined_value'] = '\n'.join(tokens)
        placeholder = (attrs or {}).get('placeholder') if attrs else None
        widget_ctx['input_placeholder'] = placeholder or 'Add state'
        attrs_copy = widget_ctx.get('attrs', {}).copy()
        attrs_copy.pop('placeholder', None)
        widget_ctx['attrs'] = attrs_copy
        if 'id' not in widget_ctx['attrs']:
            widget_ctx['attrs']['id'] = f'id_{name}'
        return context

    class Media:
        css = {
            'all': ('store/admin/tag_list_widget.css',),
        }
        js = ('store/admin/tag_list_widget.js',)


@admin.register(Fish)
class FishAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'category',
        'breed',
        'price',
        'stock_quantity',
        'is_available',
        'is_featured',
        'created_at',
    )
    list_filter = ('is_available', 'is_featured', 'category', 'breed')
    search_fields = ('name', 'description', 'category__name', 'breed__name')
    list_editable = ('is_available', 'is_featured')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Fish Details', {
            'fields': ('name', 'category', 'breed', 'description', 'image')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'size', 'weight', 'stock_quantity', 'minimum_order_quantity', 'is_available', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(FishCategory)
class FishCategoryAdmin(BaseCategoryAdmin):
    section_title = 'Fish Category'
    category_type = 'fish'


@admin.register(ComboCategory)
class ComboCategoryAdmin(BaseCategoryAdmin):
    section_title = 'Combo Offer Category'
    category_type = 'combo'


@admin.register(AccessoryCategory)
class AccessoryCategoryAdmin(BaseCategoryAdmin):
    section_title = 'Accessory Category'
    category_type = 'accessory'


@admin.register(PlantCategory)
class PlantCategoryAdmin(BaseCategoryAdmin):
    section_title = 'Plant Category'
    category_type = 'plant'


@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active', 'stock_quantity', 'display_order', 'created_at')
    list_filter = ('is_active', 'category')
    search_fields = ('name', 'description')
    list_editable = ('is_active', 'display_order')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Plant Details', {
            'fields': ('name', 'category', 'description', 'image')
        }),
        ('Inventory & Pricing', {
            'fields': ('price', 'stock_quantity', 'minimum_order_quantity', 'is_active', 'display_order')
        }),
        ('Meta', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class ShippingChargeSettingAdminForm(forms.ModelForm):
    class Meta:
        model = ShippingChargeSetting
        fields = '__all__'
        widgets = {
            'unserviceable_states': TagListWidget(attrs={
                'placeholder': 'Add state',
            })
        }
        labels = {
            'unserviceable_states': 'Delivery Not Available In (States)'
        }


@admin.register(ShippingChargeByLocation)
class ShippingChargeByLocationAdmin(admin.ModelAdmin):
    list_display = ('location_name', 'shipping_charge', 'is_active', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('location_name',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Location Details', {
            'fields': ('location_name', 'shipping_charge', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['location_name'].help_text = 'Enter the location/state/region name (e.g., Kerala, Tamil Nadu, Delhi, etc.)'
        form.base_fields['shipping_charge'].help_text = 'Enter the shipping charge amount for this location'
        return form


@admin.register(ShippingChargeSetting)
class ShippingChargeSettingAdmin(admin.ModelAdmin):
    form = ShippingChargeSettingAdminForm
    list_display = ('kerala_rate', 'default_rate', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Shipping Rates (Legacy)', {
            'fields': ('kerala_rate', 'default_rate'),
            'description': 'These rates are used as fallback. Use "Shipping Charges by Location" above for location-specific rates.'
        }),
        ('Unavailable States', {
            'fields': ('unserviceable_states',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


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


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percentage', 'max_discount_amount', 'min_order_amount', 'coupon_type', 'is_active', 'show_in_suggestions', 'force_apply', 'valid_from', 'valid_until', 'times_used', 'usage_limit')
    list_filter = ('is_active', 'show_in_suggestions', 'coupon_type', 'valid_from', 'valid_until')
    search_fields = ('code',)
    list_editable = ('is_active', 'show_in_suggestions', 'force_apply')
    readonly_fields = ('times_used', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Info', {
            'fields': ('code', 'discount_percentage', 'max_discount_amount', 'min_order_amount')
        }),
        ('Eligibility', {
            'fields': ('coupon_type', 'is_active', 'show_in_suggestions', 'force_apply', 'valid_from', 'valid_until', 'usage_limit')
        }),
        ('Usage', {
            'fields': ('times_used', 'created_by'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'is_published', 'published_at', 'created_at')
    list_filter = ('is_published', 'published_at')
    search_fields = ('title', 'sub_title', 'content', 'author__username')
    readonly_fields = ('created_at', 'updated_at')


# Minimal admin registration for combos so admin add URL exists
class ComboItemInline(admin.TabularInline):
    model = ComboItem
    extra = 1


@admin.register(ComboOffer)
class ComboOfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'bundle_price', 'category', 'is_active', 'show_on_homepage', 'created_at')
    list_filter = ('is_active', 'show_on_homepage', 'category')
    search_fields = ('title', 'description', 'category__name')
    list_editable = ('is_active', 'show_on_homepage')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Offer Details', {
            'fields': ('title', 'description', 'bundle_price', 'category')
        }),
        ('Display Options', {
            'fields': ('is_active', 'show_on_homepage')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            kwargs['queryset'] = Category.objects.filter(category_type='combo').order_by('name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


