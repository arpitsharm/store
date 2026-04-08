from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home_view, name='home'),
    
    # About
    path('about/', views.about_view, name='about'),
    
    # Products
    path('products/', views.product_list_view, name='product_list'),
    path('products/<slug:category_slug>/', views.product_list_view, name='category_products'),
    path('product/<slug:slug>/', views.product_detail_view, name='product_detail'),
    
    # Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('cart/apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('cart/remove-coupon/', views.remove_coupon, name='remove_coupon'),
    
    # Checkout & Orders
    path('checkout/', views.checkout_view, name='checkout'),
    path('order/<str:order_number>/', views.order_detail_view, name='order_detail'),
    path('my-orders/', views.order_history_view, name='order_history'),
    path('order/<int:order_id>/cancel/', views.cancel_order_view, name='cancel_order'),
    path('order/<int:order_id>/return/', views.return_order_view, name='return_order'),
    
    # Wishlist
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
    
    # Reviews
    path('review/edit/<int:review_id>/', views.edit_review_view, name='edit_review'),
    
    # Addresses
    path('addresses/', views.address_list_view, name='address_list'),
    path('addresses/add/', views.add_address_view, name='add_address'),
    path('addresses/<int:address_id>/edit/', views.edit_address_view, name='edit_address'),
    path('addresses/<int:address_id>/set-default/', views.set_default_address_view, name='set_default_address'),
    
    # Complaints
    path('complaints/', views.complaint_list_view, name='complaint_list'),
    path('complaints/create/', views.create_complaint_view, name='create_complaint'),
    
    # Payment Gateway
    path('payment/paytm/<int:order_id>/', views.paytm_payment_view, name='paytm_payment'),
    path('payment/paytm/callback/<int:order_id>/', views.paytm_callback_view, name='paytm_callback'),
    path('payment/paytm/process/<int:order_id>/', views.process_paytm_payment, name='process_paytm_payment'),
]
