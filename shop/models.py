from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit
from PIL import Image
import os
import random
import string

# ===== IMAGE VALIDATION =====
def validate_image(file):
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in valid_extensions:
        raise ValidationError('Only JPG, PNG, and WebP images are allowed.')
    
    if file.size > 5 * 1024 * 1024:
        raise ValidationError('Image must be under 5MB.')
    
    try:
        img = Image.open(file)
        img.verify()
    except Exception:
        raise ValidationError('Invalid image file.')


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'Categories'


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    base_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    
    main_image = models.ImageField(
        upload_to='products/', 
        blank=True, 
        null=True,
        validators=[validate_image]
    )
    
    thumbnail = ImageSpecField(
        source='main_image',
        processors=[ResizeToFit(300, 300)],
        format='JPEG',
        options={'quality': 70}
    )
    medium_image = ImageSpecField(
        source='main_image',
        processors=[ResizeToFit(600, 600)],
        format='JPEG',
        options={'quality': 80}
    )
    large_image = ImageSpecField(
        source='main_image',
        processors=[ResizeToFit(900, 900)],
        format='JPEG',
        options={'quality': 85}
    )
    
    images = models.JSONField(default=list, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('product_detail', args=[self.slug])
    
    class Meta:
        ordering = ['-created_at']


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    color = models.CharField(max_length=50, blank=True)
    storage = models.CharField(max_length=50, blank=True)
    additional_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    sku = models.CharField(max_length=100, unique=True, blank=True)
    
    def __str__(self):
        name = self.product.name
        if self.color:
            name += f" - {self.color}"
        if self.storage:
            name += f" ({self.storage})"
        return name
    
    @property
    def total_price(self):
        return self.product.base_price + self.additional_price


class Wishlist(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('product', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}★)"


# ============================================================
# ===== COUPON SYSTEM =====
# ============================================================

class Coupon(models.Model):
    """
    Custom coupon model with 9-digit codes
    """
    # 9-digit code (e.g., "ABC123XYZ")
    code = models.CharField(
        max_length=9,
        unique=True,
        db_index=True,
        help_text="9-character alphanumeric code (e.g., ABC123XYZ)"
    )
    
    # Discount percentage (e.g., 10 for 10%)
    discount_percent = models.PositiveIntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Discount percentage (e.g., 10 for 10%)"
    )
    
    # Minimum order amount to use coupon (KES 1,000)
    minimum_order = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1000.00,
        help_text="Minimum order amount to apply this coupon"
    )
    
    # Maximum discount amount (optional)
    max_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Maximum discount amount (leave blank for no limit)"
    )
    
    # Usage limits
    max_uses = models.PositiveIntegerField(
        default=0,
        help_text="Maximum number of times this coupon can be used (0 = unlimited)"
    )
    used_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this coupon has been used"
    )
    
    # User-specific coupon (optional)
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="If set, only this user can use this coupon"
    )
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(
        help_text="Coupon expiry date"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Description for admin
    description = models.CharField(
        max_length=255,
        blank=True,
        help_text="Internal description for admin reference"
    )
    
    def __str__(self):
        return f"{self.code} - {self.discount_percent}% off"
    
    def is_valid(self, cart_total, user=None):
        """
        Check if coupon is valid for use
        """
        now = timezone.now()
        
        # Check basic validity
        if not self.is_active:
            return False, "This coupon is no longer active."
        
        if self.valid_from > now:
            return False, "This coupon is not yet valid."
        
        if self.valid_to < now:
            return False, "This coupon has expired."
        
        if cart_total < self.minimum_order:
            return False, f"Minimum order of KES {self.minimum_order:,.2f} required."
        
        if self.max_uses > 0 and self.used_count >= self.max_uses:
            return False, "This coupon has been used the maximum number of times."
        
        if self.user and user and self.user != user:
            return False, "This coupon is not valid for your account."
        
        return True, "Valid"
    
    def calculate_discount(self, total):
        """
        Calculate the discount amount for a given total
        """
        discount = (self.discount_percent / 100) * total
        
        # Apply max discount limit if set
        if self.max_discount and discount > self.max_discount:
            discount = self.max_discount
        
        return discount
    
    def generate_code():
        """Generate a random 9-digit alphanumeric code"""
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choices(chars, k=9))
    
    def save(self, *args, **kwargs):
        if not self.code:
            # Generate a unique code if not provided
            while True:
                new_code = self.generate_code()
                if not Coupon.objects.filter(code=new_code).exists():
                    self.code = new_code
                    break
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_at']


class UsedCoupon(models.Model):
    """
    Track which users have used which coupons
    """
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='used_coupons')
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    order = models.ForeignKey('checkout.Order', on_delete=models.CASCADE, related_name='used_coupons')
    used_at = models.DateTimeField(auto_now_add=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    order_total = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.coupon.code} - {self.order.order_id}"
    
    class Meta:
        ordering = ['-used_at']
        unique_together = ('coupon', 'order')