from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('verify-otp/<int:user_id>/', views.verify_otp_view, name='verify_otp'),
    path('resend-otp/<int:user_id>/', views.resend_otp_view, name='resend_otp'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/<int:user_id>/', views.reset_password_view, name='reset_password'),
    
    # Home
    path('', views.home_view, name='home'),
    
    # Customer Routes
    path('fishes/', views.customer_fish_list_view, name='fish_list'),
    path('fish/<int:fish_id>/', views.fish_detail_view, name='fish_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:fish_id>/', views.add_to_cart_view, name='add_to_cart'),
    path('update-cart/<int:cart_id>/', views.update_cart_view, name='update_cart'),
    path('remove-cart/<int:cart_id>/', views.remove_from_cart_view, name='remove_cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('orders/', views.customer_orders_view, name='customer_orders'),
    path('order/<int:order_id>/', views.order_detail_view, name='order_detail'),
    
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
    
    # Admin Routes (using store-admin prefix to avoid conflict with Django admin)
    path('store-admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('store-admin/staff/', views.admin_staff_list_view, name='admin_staff_list'),
    path('store-admin/add-staff/', views.add_staff_view, name='add_staff'),
    path('store-admin/remove-staff/<int:user_id>/', views.remove_staff_view, name='remove_staff'),
    path('store-admin/categories/', views.admin_categories_view, name='admin_categories'),
    path('store-admin/add-category/', views.admin_add_category_view, name='admin_add_category'),
    path('store-admin/delete-category/<int:category_id>/', views.admin_delete_category_view, name='admin_delete_category'),
    path('store-admin/breeds/', views.admin_breeds_view, name='admin_breeds'),
    path('store-admin/add-breed/', views.admin_add_breed_view, name='admin_add_breed'),
    path('store-admin/delete-breed/<int:breed_id>/', views.admin_delete_breed_view, name='admin_delete_breed'),
    path('store-admin/fishes/', views.admin_fishes_view, name='admin_fishes'),
    path('store-admin/add-fish/', views.admin_add_fish_view, name='admin_add_fish'),
    path('store-admin/delete-fish/<int:fish_id>/', views.admin_delete_fish_view, name='admin_delete_fish'),
    path('store-admin/orders/', views.admin_orders_view, name='admin_orders'),
    path('store-admin/order/<int:order_id>/', views.admin_order_detail_view, name='admin_order_detail'),
    path('store-admin/users/', views.admin_users_view, name='admin_users'),
    path('store-admin/block-user/<int:user_id>/', views.block_user_view, name='block_user'),
    path('store-admin/unblock-user/<int:user_id>/', views.unblock_user_view, name='unblock_user'),
    path('store-admin/export-orders/', views.export_orders_excel_view, name='export_orders_excel'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('edit-profile/', views.edit_profile_view, name='edit_profile'),
]

