from django.urls import path
from . import views
from . import stripe_integration

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    # Registration OTP (session-based, no user created yet)
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # Debug email test endpoint (only works when DEBUG=True)
    path('test-email/', views.test_email_view, name='test_email'),
    path('email-debug/', views.email_config_view, name='email_debug'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/<int:user_id>/', views.reset_password_view, name='reset_password'),
    
    # Home
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    # Blog
    path('blog/', views.blog_list_view, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail_view, name='blog_detail'),
    
    # Customer Routes
    path('fishes/', views.customer_fish_list_view, name='fish_list'),
    path('fish/<int:fish_id>/', views.fish_detail_view, name='fish_detail'),
    # Accessories (customer)
    path('accessories/', views.customer_accessories_view, name='accessories'),
    path('accessory/<int:accessory_id>/', views.accessory_detail_view, name='accessory_detail'),
    path('accessory/add-to-cart/<int:accessory_id>/', views.add_accessory_to_cart_view, name='add_accessory_to_cart'),
    path('accessories/add/', views.accessories_add_view, name='accessories_add'),
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:fish_id>/', views.add_to_cart_view, name='add_to_cart'),
    path('update-cart/<int:cart_id>/', views.update_cart_view, name='update_cart'),
    path('remove-cart/<int:cart_id>/', views.remove_from_cart_view, name='remove_cart'),
    path('update-accessory-cart/<int:accessory_cart_id>/', views.update_accessory_cart_view, name='update_accessory_cart'),
    path('remove-accessory-cart/<int:accessory_cart_id>/', views.remove_accessory_cart_view, name='remove_accessory_cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('checkout/create-draft/', views.create_draft_order, name='create_draft_order'),
    path('apply-coupon/', views.apply_coupon_view, name='apply_coupon'),
    path('remove-coupon/', views.remove_coupon_view, name='remove_coupon'),
    path('orders/', views.customer_orders_view, name='customer_orders'),
    path('order/<int:order_id>/', views.order_detail_view, name='order_detail'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation_view, name='order_confirmation'),
    path('order/<int:order_id>/cancel/', views.cancel_order_view, name='cancel_order'),
    path('order/<int:order_id>/review/', views.submit_review_view, name='submit_review'),
    path('upi-payment/<int:order_id>/', views.upi_payment_view, name='upi_payment'),
    path('verify-upi/<int:order_id>/', views.verify_upi_payment, name='verify_upi_payment'),
    # Payment endpoints (Stripe-backed integration is the primary path now)
    # Stripe payment endpoints
    path('payments/stripe/create/<int:order_id>/', stripe_integration.create_stripe_payment, name='create_stripe_payment'),
    path('payments/stripe/webhook/', stripe_integration.stripe_webhook, name='stripe_webhook'),
    path('payments/stripe/verify/', stripe_integration.verify_stripe_payment, name='verify_stripe_payment'),
    
    # Staff Routes
    path('staff/dashboard/', views.staff_dashboard_view, name='staff_dashboard'),
    path('staff/fishes/', views.staff_fish_list_view, name='staff_fish_list'),
    path('staff/categories/', views.staff_categories_view, name='staff_categories'),
    path('staff/add-category/', views.add_category_view, name='add_category'),
    path('staff/delete-category/<int:category_id>/', views.delete_category_view, name='delete_category'),
    path('staff/breeds/', views.staff_breeds_view, name='staff_breeds'),
    path('staff/add-breed/', views.add_breed_view, name='add_breed'),
    path('staff/delete-breed/<int:breed_id>/', views.delete_breed_view, name='delete_breed'),
    path('staff/add-fish/', views.add_fish_view, name='add_fish'),
    path('staff/edit-fish/<int:fish_id>/', views.edit_fish_view, name='edit_fish'),
    path('staff/delete-fish/<int:fish_id>/', views.delete_fish_view, name='delete_fish'),
    path('staff/fish/<int:fish_id>/media/', views.staff_fish_media_view, name='staff_fish_media'),
    path('staff/fish/media/delete/<int:media_id>/', views.staff_delete_fish_media_view, name='staff_delete_fish_media'),
    path('staff/fish/media/<int:media_id>/edit/', views.staff_edit_fish_media_view, name='staff_edit_fish_media'),
    # Accessories (staff)
    path('staff/accessories/', views.staff_accessories_view, name='staff_accessories'),
    path('staff/add-accessory/', views.add_accessory_view, name='add_accessory'),
    path('staff/edit-accessory/<int:accessory_id>/', views.edit_accessory_view, name='edit_accessory'),
    path('staff/delete-accessory/<int:accessory_id>/', views.delete_accessory_view, name='delete_accessory'),
    
    # Admin Routes (using store-admin prefix to avoid conflict with Django admin)
    path('store-admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('store-admin/staff/', views.admin_staff_list_view, name='admin_staff_list'),
    path('store-admin/add-staff/', views.add_staff_view, name='add_staff'),
    path('store-admin/remove-staff/<int:user_id>/', views.remove_staff_view, name='remove_staff'),
    path('store-admin/block-staff/<int:user_id>/', views.block_staff_view, name='block_staff'),
    path('store-admin/unblock-staff/<int:user_id>/', views.unblock_staff_view, name='unblock_staff'),
    path('store-admin/categories/', views.admin_categories_view, name='admin_categories'),
    path('store-admin/add-category/', views.admin_add_category_view, name='admin_add_category'),
    path('store-admin/delete-category/<int:category_id>/', views.admin_delete_category_view, name='admin_delete_category'),
    path('store-admin/breeds/', views.admin_breeds_view, name='admin_breeds'),
    path('store-admin/add-breed/', views.admin_add_breed_view, name='admin_add_breed'),
    path('store-admin/delete-breed/<int:breed_id>/', views.admin_delete_breed_view, name='admin_delete_breed'),
    path('store-admin/fishes/', views.admin_fishes_view, name='admin_fishes'),
    path('store-admin/add-fish/', views.admin_add_fish_view, name='admin_add_fish'),
    path('store-admin/delete-fish/<int:fish_id>/', views.admin_delete_fish_view, name='admin_delete_fish'),
    path('store-admin/fish/<int:fish_id>/media/', views.admin_fish_media_view, name='admin_fish_media'),
    path('store-admin/fish/media/delete/<int:media_id>/', views.admin_delete_fish_media_view, name='admin_delete_fish_media'),
    path('store-admin/fish/media/<int:media_id>/edit/', views.admin_edit_fish_media_view, name='admin_edit_fish_media'),
    # Accessories (admin)
    path('store-admin/accessories/', views.admin_accessories_view, name='admin_accessories'),
    path('store-admin/add-accessory/', views.admin_add_accessory_view, name='admin_add_accessory'),
    path('store-admin/edit-accessory/<int:accessory_id>/', views.admin_edit_accessory_view, name='admin_edit_accessory'),
    path('store-admin/delete-accessory/<int:accessory_id>/', views.admin_delete_accessory_view, name='admin_delete_accessory'),
    # Services Management
    path('store-admin/services/', views.admin_services_view, name='admin_services'),
    path('store-admin/add-service/', views.admin_add_service_view, name='admin_add_service'),
    path('store-admin/edit-service/<int:service_id>/', views.admin_edit_service_view, name='admin_edit_service'),
    path('store-admin/delete-service/<int:service_id>/', views.admin_delete_service_view, name='admin_delete_service'),
    # Contact Info Management
    path('store-admin/contact/', views.admin_contact_view, name='admin_contact'),
    path('store-admin/add-contact/', views.admin_add_contact_view, name='admin_add_contact'),
    path('store-admin/edit-contact/<int:contact_id>/', views.admin_edit_contact_view, name='admin_edit_contact'),
    # Review Management
    path('store-admin/reviews/', views.admin_reviews_view, name='admin_reviews'),
    path('store-admin/approve-review/<int:review_id>/', views.admin_approve_review, name='admin_approve_review'),
    path('store-admin/reject-review/<int:review_id>/', views.admin_reject_review, name='admin_reject_review'),
    path('store-admin/orders/', views.admin_orders_view, name='admin_orders'),
    path('store-admin/orders/ajax/', views.admin_orders_ajax_view, name='admin_orders_ajax'),
    path('store-admin/order/<int:order_id>/', views.admin_order_detail_view, name='admin_order_detail'),
    path('store-admin/users/', views.admin_users_view, name='admin_users'),
    path('store-admin/toggle-favorite/<int:user_id>/', views.toggle_favorite_user_view, name='toggle_favorite_user'),
    path('store-admin/block-user/<int:user_id>/', views.block_user_view, name='block_user'),
    path('store-admin/unblock-user/<int:user_id>/', views.unblock_user_view, name='unblock_user'),
    path('store-admin/export-orders/', views.export_orders_excel_view, name='export_orders_excel'),
    # Coupon Management
    path('store-admin/coupons/', views.admin_coupons_view, name='admin_coupons'),
    path('store-admin/add-coupon/', views.admin_add_coupon_view, name='admin_add_coupon'),
    path('store-admin/edit-coupon/<int:coupon_id>/', views.admin_edit_coupon_view, name='admin_edit_coupon'),
    path('store-admin/delete-coupon/<int:coupon_id>/', views.admin_delete_coupon_view, name='admin_delete_coupon'),
    path('store-admin/toggle-coupon/<int:coupon_id>/', views.admin_toggle_coupon_view, name='admin_toggle_coupon'),
        # Limited Offers (admin)
        path('store-admin/limited-offers/', views.admin_limited_offers_view, name='admin_limited_offers'),
        path('store-admin/limited-offers/add/', views.admin_add_limited_offer_view, name='admin_add_limited_offer'),
        path('store-admin/limited-offers/<int:offer_id>/edit/', views.admin_edit_limited_offer_view, name='admin_edit_limited_offer'),
        path('store-admin/limited-offers/<int:offer_id>/toggle/', views.admin_toggle_limited_offer_view, name='admin_toggle_limited_offer'),
        path('store-admin/limited-offers/<int:offer_id>/delete/', views.admin_delete_limited_offer_view, name='admin_delete_limited_offer'),
        # Blogs (site-admin)
        path('store-admin/blogs/', views.admin_blogs_view, name='admin_blogs'),
        path('store-admin/blogs/add/', views.admin_add_blog_view, name='admin_add_blog'),
        path('store-admin/blogs/<int:post_id>/edit/', views.admin_edit_blog_view, name='admin_edit_blog'),
        path('store-admin/blogs/<int:post_id>/delete/', views.admin_delete_blog_view, name='admin_delete_blog'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('edit-profile/', views.edit_profile_view, name='edit_profile'),
    path('change-password/', views.change_password_view, name='change_password'),
]

