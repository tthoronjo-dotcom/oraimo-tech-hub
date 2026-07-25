from shop.models import ProductVariant

class Basket:
    def __init__(self, request):
        self.session = request.session
        basket = self.session.get('basket', {})
        self.basket = basket
        self.request = request
    
    def add(self, variant_id, quantity=1):
        variant_id = str(variant_id)
        
        # If item already exists in session, update quantity
        if variant_id in self.basket:
            self.basket[variant_id]['quantity'] += quantity
        else:
            # Get variant and add to basket
            variant = ProductVariant.objects.get(id=variant_id)
            self.basket[variant_id] = {
                'variant_id': variant_id,
                'product_id': variant.product.id,
                'name': str(variant),
                'price': float(variant.total_price),
                'quantity': quantity,
                'image': variant.product.main_image.url if variant.product.main_image else '',
            }
        
        # Save session and sync with user
        self.save()
        
        # Only sync with user if authenticated and session basket has items
        if self.request.user.is_authenticated:
            self._sync_with_user()
    
    def remove(self, variant_id):
        variant_id = str(variant_id)
        if variant_id in self.basket:
            del self.basket[variant_id]
            self.save()
            if self.request.user.is_authenticated:
                self._sync_with_user()
    
    def update_quantity(self, variant_id, quantity):
        variant_id = str(variant_id)
        if variant_id in self.basket:
            if quantity <= 0:
                self.remove(variant_id)
            else:
                self.basket[variant_id]['quantity'] = quantity
                self.save()
                if self.request.user.is_authenticated:
                    self._sync_with_user()
    
    def get_total_price(self):
        return sum(item['price'] * item['quantity'] for item in self.basket.values())
    
    def get_total_items(self):
        return sum(item['quantity'] for item in self.basket.values())
    
    def clear(self):
        self.session['basket'] = {}
        self.session.modified = True
        self.basket = {}
        if self.request.user.is_authenticated:
            self._sync_with_user()
    
    def save(self):
        self.session['basket'] = self.basket
        self.session.modified = True
    
    def _sync_with_user(self):
        """Sync basket with user's saved basket - uses update_or_create to prevent duplicates"""
        from .models import SavedBasketItem
        
        # Get all current basket items
        for variant_id, item in self.basket.items():
            SavedBasketItem.objects.update_or_create(
                user=self.request.user,
                variant_id=int(variant_id),
                defaults={'quantity': item['quantity']}
            )
        
        # Remove items from user's saved basket that are no longer in session basket
        user_variant_ids = [int(vid) for vid in self.basket.keys()]
        SavedBasketItem.objects.filter(
            user=self.request.user
        ).exclude(
            variant_id__in=user_variant_ids
        ).delete()
    
    def merge_with_user_basket(self, user):
        """Merge session basket with user's saved basket"""
        from .models import SavedBasketItem
        
        saved_items = SavedBasketItem.objects.filter(user=user)
        
        for saved in saved_items:
            variant_id = str(saved.variant.id)
            if variant_id in self.basket:
                self.basket[variant_id]['quantity'] += saved.quantity
            else:
                variant = saved.variant
                self.basket[variant_id] = {
                    'variant_id': variant_id,
                    'product_id': variant.product.id,
                    'name': str(variant),
                    'price': float(variant.total_price),
                    'quantity': saved.quantity,
                    'image': variant.product.main_image.url if variant.product.main_image else '',
                }
        
        self.save()
        saved_items.delete()
    
    def save_to_user(self, user):
        """Save current basket to user's saved basket - FIXED to avoid duplicates"""
        from .models import SavedBasketItem
        
        # Use update_or_create to avoid duplicate key errors
        for item in self.basket.values():
            SavedBasketItem.objects.update_or_create(
                user=user,
                variant_id=int(item['variant_id']),
                defaults={'quantity': item['quantity']}
            )
    
    def __iter__(self):
        for item in self.basket.values():
            yield item
    
    def __len__(self):
        return len(self.basket)
