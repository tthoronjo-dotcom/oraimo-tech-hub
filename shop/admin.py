from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Category, Product, ProductVariant, Wishlist, ProductReview, Coupon, UsedCoupon


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'base_price', 'is_active', 'featured', 'created_at']
    list_filter = ['category', 'is_active', 'featured']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'color', 'storage', 'additional_price', 'sku']
    list_filter = ['product', 'color']
    search_fields = ['product__name', 'sku']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'added_at']
    search_fields = ['user__username', 'product__name']


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'rating']
    search_fields = ['product__name', 'user__username']


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'discount_percent', 'minimum_order', 
        'used_count', 'max_uses', 'is_active', 'valid_to', 'status_badge'
    ]
    list_filter = ['is_active', 'valid_from', 'valid_to']
    search_fields = ['code', 'description']
    readonly_fields = ['used_count', 'created_at', 'code']
    
    fieldsets = (
        ('Coupon Information', {
            'fields': ('code', 'description', 'discount_percent', 'minimum_order', 'max_discount')
        }),
        ('Usage Limits', {
            'fields': ('max_uses', 'used_count', 'user')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_to', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    def status_badge(self, obj):
        now = timezone.now()
        if not obj.is_active:
            return format_html('<span style="color: red;">❌ Inactive</span>')
        elif obj.valid_to < now:
            return format_html('<span style="color: orange;">⏰ Expired</span>')
        elif obj.valid_from > now:
            return format_html('<span style="color: blue;">⏳ Pending</span>')
        else:
            return format_html('<span style="color: green;">✅ Active</span>')
    status_badge.short_description = 'Status'
    
    actions = ['activate_coupons', 'deactivate_coupons']
    
    def activate_coupons(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} coupons activated.")
    activate_coupons.short_description = "Activate selected coupons"
    
    def deactivate_coupons(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} coupons deactivated.")
    deactivate_coupons.short_description = "Deactivate selected coupons"


@admin.register(UsedCoupon)
class UsedCouponAdmin(admin.ModelAdmin):
    list_display = ['coupon', 'order', 'user', 'discount_amount', 'order_total', 'used_at']
    list_filter = ['used_at']
    search_fields = ['coupon__code', 'order__order_id']
    readonly_fields = ['coupon', 'order', 'user', 'discount_amount', 'order_total', 'used_at']