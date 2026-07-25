from django.core.management.base import BaseCommand
from shop.models import Product

class Command(BaseCommand):
    help = 'Generate thumbnails for all products'

    def handle(self, *args, **options):
        products = Product.objects.filter(main_image__isnull=False)
        count = 0
        
        for product in products:
            try:
                # Accessing the thumbnail generates it
                if product.main_image:
                    # Force thumbnail generation
                    thumb = product.thumbnail
                    medium = product.medium_image
                    large = product.large_image
                    count += 1
                    self.stdout.write(f"Generated thumbnails for: {product.name}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error for {product.name}: {e}"))
        
        self.stdout.write(self.style.SUCCESS(f"Generated thumbnails for {count} products"))
