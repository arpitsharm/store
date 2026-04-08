from django.contrib import admin
from .models import Category, Product, Review, Cart, CartItem, Wishlist, Order, OrderItem, Coupon, CustomerProfile


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock_quantity', 'is_featured', 'is_available']
    list_filter = ['category', 'is_featured', 'is_available']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'approved', 'created_at']
    list_filter = ['approved', 'rating']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'total_amount', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method']


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'is_active', 'valid_until']
    list_filter = ['is_active', 'discount_type']


admin.site.register([Cart, CartItem, Wishlist, CustomerProfile])
