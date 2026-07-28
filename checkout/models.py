from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from shop.models import ProductVariant, Coupon
from django.utils import timezone

class Order(models.Model):
    # Keep existing payment status but simplify for COD
    PAYMENT_STATUS = [
        ('pending', 'Pending Payment'),  # Changed from 'No Payment Made'
        ('partial', 'Partial Payment'),   # Keep for flexibility
        ('collected', 'Payment Collected on Delivery'),  # NEW - COD collected
        ('failed', 'Payment Failed'),      # NEW - Payment failed
        ('cancelled', 'Cancelled'),
    ]
    
    # Keep existing delivery status exactly as is
    DELIVERY_STATUS = [
        ('pending', 'Order Placed'),
        ('confirmed', 'Confirmed'),
        ('picked', 'Picked by Rider'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
    ]
    
    # Keep all existing fields
    order_id = models.CharField(max_length=20, unique=True, db_index=True)
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=15, db_index=True)
    customer_email = models.EmailField(blank=True)
    delivery_location = models.CharField(max_length=100)
    delivery_address = models.TextField()
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    remaining_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS, default='pending')
    
    is_cbd = models.BooleanField(default=False)
    marketing_consent = models.BooleanField(default=False)
    
    # NEW: COD specific fields
    cod_collected_at = models.DateTimeField(
        blank=True, 
        null=True,
        help_text="When payment was collected on delivery"
    )
    cod_collected_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='collected_payments',
        help_text="Admin who marked payment as collected"
    )
    
    # NEW: Delivery notes for the rider
    delivery_notes = models.TextField(
        blank=True,
        help_text="Special instructions for delivery team"
    )
    
    # ===== COUPON FIELDS =====
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        help_text="Coupon applied to this order"
    )
    coupon_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Discount amount applied from coupon"
    )
    coupon_code_used = models.CharField(
        max_length=9,
        blank=True,
        help_text="The coupon code that was applied"
    )
    
    # Keep existing payment fields but make them optional/blank
    mpesa_receipt = models.CharField(max_length=100, blank=True)
    delivery_fee_receipt = models.CharField(max_length=100, blank=True)
    checkout_request_id = models.CharField(max_length=100, blank=True)
    pesapal_tracking_id = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.order_id} - {self.customer_phone}"
    
    def save(self, *args, **kwargs):
        # For COD, remaining_balance is the full amount until collected
        if self.payment_status == 'collected':
            self.amount_paid = self.total_amount
            self.remaining_balance = 0
        elif self.payment_status in ['pending', 'partial']:
            # For COD, payment_status 'pending' means no payment yet
            self.remaining_balance = self.total_amount - self.amount_paid
        super().save(*args, **kwargs)
    
    def get_payment_status_display_name(self):
        status_display = {
            'pending': 'Pay on Delivery (Pending)',
            'partial': 'Partial Payment Made',
            'collected': '✅ Payment Collected on Delivery',
            'failed': '❌ Payment Failed',
            'cancelled': 'Order Cancelled',
        }
        return status_display.get(self.payment_status, self.payment_status)
    
    def get_delivery_status_display_name(self):
        delivery_status_display = {
            'pending': 'Order Placed',
            'confirmed': 'Order Confirmed',
            'picked': 'Picked by Rider',
            'out_for_delivery': 'Out for Delivery',
            'delivered': 'Delivered! Thank you for shopping.',
        }
        return delivery_status_display.get(self.delivery_status, self.delivery_status)
    
    # NEW: Helper properties for COD
    @property
    def is_cod_pending(self):
        """Check if payment is pending for COD"""
        return self.payment_status == 'pending'
    
    @property
    def is_cod_collected(self):
        """Check if payment was collected"""
        return self.payment_status == 'collected'
    
    def mark_cod_as_collected(self, user=None):
        """Mark order payment as collected on delivery"""
        self.payment_status = 'collected'
        self.amount_paid = self.total_amount
        self.remaining_balance = 0
        self.cod_collected_at = timezone.now()
        if user:
            self.cod_collected_by = user
        self.save()
    
    def mark_cod_as_failed(self):
        """Mark order payment as failed"""
        self.payment_status = 'failed'
        self.save()
    
    # ===== COUPON METHODS =====
    def apply_coupon(self, coupon_code, basket_total):
        """
        Apply a coupon to this order
        """
        from shop.models import Coupon, UsedCoupon
        
        try:
            coupon = Coupon.objects.get(code=coupon_code.upper(), is_active=True)
            
            # Check if valid
            is_valid, message = coupon.is_valid(basket_total)
            if not is_valid:
                return False, message
            
            # Check if coupon already used on this order
            if UsedCoupon.objects.filter(coupon=coupon, order=self).exists():
                return False, "This coupon has already been applied to this order."
            
            # Calculate discount
            discount = coupon.calculate_discount(self.subtotal)
            
            # Apply discount
            self.coupon = coupon
            self.coupon_discount = discount
            self.coupon_code_used = coupon.code
            self.total_amount = self.subtotal + self.delivery_fee - discount
            self.save()
            
            return True, f"Coupon applied! You saved KES {discount:,.2f}"
            
        except Coupon.DoesNotExist:
            return False, "Invalid coupon code. Please check and try again."
    
    def get_coupon_discount_display(self):
        """
        Get the coupon discount as a percentage with label
        """
        if self.coupon:
            return f"{self.coupon.discount_percent}% off"
        return "No coupon applied"
    
    @property
    def has_coupon(self):
        """Check if order has a coupon applied"""
        return self.coupon is not None
    
    @property
    def formatted_discount(self):
        """Get the discount amount formatted"""
        return f"KES {self.coupon_discount:,.2f}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)
    variant_name = models.CharField(max_length=200, blank=True)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    @property
    def total(self):
        return self.price * self.quantity