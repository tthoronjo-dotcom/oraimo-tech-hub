from django.db import models
from django.contrib.auth.models import User
from shop.models import ProductVariant

class SavedBasketItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_basket')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'variant')

    def __str__(self):
        return f"{self.user.username} - {self.variant.product.name}"