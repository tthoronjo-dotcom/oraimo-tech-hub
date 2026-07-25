from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Order, OrderItem
from core.emails import send_order_confirmation_email

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'variant_name', 'quantity', 'price')
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_id', 
        'customer_name', 
        'customer_phone', 
        'total_amount', 
        'payment_status_display', 
        'delivery_status_display',
        'created_at'
    )
    
    list_filter = ('payment_status', 'delivery_status', 'is_cbd', 'created_at')
    search_fields = ('order_id', 'customer_name', 'customer_phone', 'customer_email')
    inlines = [OrderItemInline]
    readonly_fields = ('order_id', 'created_at', 'updated_at', 'subtotal', 'total_amount')
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_id', 'customer_name', 'customer_phone', 'customer_email')
        }),
        ('Delivery Details', {
            'fields': ('delivery_location', 'delivery_address', 'is_cbd', 'delivery_notes')
        }),
        ('Payment on Delivery', {
            'fields': ('payment_status', 'cod_collected_at', 'cod_collected_by')
        }),
        ('Financial Details', {
            'fields': ('subtotal', 'delivery_fee', 'total_amount', 'amount_paid', 'remaining_balance')
        }),
        ('Marketing Consent', {
            'fields': ('marketing_consent',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def payment_status_display(self, obj):
        """Display payment status with colored badges"""
        status_colors = {
            'pending': 'warning',
            'partial': 'info',
            'collected': 'success',
            'failed': 'danger',
            'cancelled': 'secondary',
        }
        status_labels = {
            'pending': '💰 Pending Payment',
            'partial': '💳 Partial Payment',
            'collected': '✅ Payment Collected',
            'failed': '❌ Payment Failed',
            'cancelled': '🚫 Cancelled',
        }
        color = status_colors.get(obj.payment_status, 'secondary')
        label = status_labels.get(obj.payment_status, obj.payment_status)
        return format_html(f'<span class="badge bg-{color}">{label}</span>')
    payment_status_display.short_description = 'Payment Status'
    
    def delivery_status_display(self, obj):
        """Display delivery status with colored badges"""
        status_colors = {
            'pending': 'secondary',
            'confirmed': 'info',
            'picked': 'primary',
            'out_for_delivery': 'warning',
            'delivered': 'success',
        }
        color = status_colors.get(obj.delivery_status, 'secondary')
        label = obj.get_delivery_status_display()
        return format_html(f'<span class="badge bg-{color}">{label}</span>')
    delivery_status_display.short_description = 'Delivery Status'
    
    actions = [
        'mark_as_confirmed', 
        'mark_as_picked', 
        'mark_as_out_for_delivery', 
        'mark_as_delivered',
        'mark_payment_as_collected',
        'mark_payment_as_failed'
    ]
    
    def mark_as_confirmed(self, request, queryset):
        queryset.update(delivery_status='confirmed')
        for order in queryset:
            if order.customer_email:
                send_order_confirmation_email(order)
        self.message_user(request, f"✅ {queryset.count()} orders marked as confirmed.")
    mark_as_confirmed.short_description = "✅ Mark as Confirmed"
    
    def mark_as_picked(self, request, queryset):
        queryset.update(delivery_status='picked')
        self.message_user(request, f"✅ {queryset.count()} orders marked as picked by rider.")
    mark_as_picked.short_description = "✅ Mark as Picked by Rider"
    
    def mark_as_out_for_delivery(self, request, queryset):
        queryset.update(delivery_status='out_for_delivery')
        self.message_user(request, f"✅ {queryset.count()} orders marked as out for delivery.")
    mark_as_out_for_delivery.short_description = "✅ Mark as Out for Delivery"
    
    def mark_as_delivered(self, request, queryset):
        queryset.update(delivery_status='delivered')
        self.message_user(request, f"✅ {queryset.count()} orders marked as delivered.")
    mark_as_delivered.short_description = "✅ Mark as Delivered"
    
    def mark_payment_as_collected(self, request, queryset):
        count = 0
        for order in queryset:
            if order.payment_status != 'collected':
                order.payment_status = 'collected'
                order.amount_paid = order.total_amount
                order.remaining_balance = 0
                order.cod_collected_at = timezone.now()
                order.cod_collected_by = request.user
                order.save()
                count += 1
        self.message_user(request, f"💰 Payment marked as collected for {count} orders.")
    mark_payment_as_collected.short_description = "💰 Mark Payment as Collected"
    
    def mark_payment_as_failed(self, request, queryset):
        queryset.update(payment_status='failed')
        self.message_user(request, f"❌ {queryset.count()} orders marked as payment failed.")
    mark_payment_as_failed.short_description = "❌ Mark Payment as Failed"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cod_collected_by')
