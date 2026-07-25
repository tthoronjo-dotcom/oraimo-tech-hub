import json
import os
import shutil
import django
from django.core.files import File
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from shop.models import Category, Product, ProductVariant

# Configuration
MEDIA_ROOT = settings.MEDIA_ROOT
IMAGE_SOURCE_FOLDER = r"C:\Users\Hp\Desktop\product_images"  # Change this to where your images are
IMAGE_DEST_FOLDER = os.path.join(MEDIA_ROOT, 'products')

# Create destination folder if it doesn't exist
os.makedirs(IMAGE_DEST_FOLDER, exist_ok=True)

# Load data
with open('product_data.json', 'r') as f:
    data = json.load(f)

print(f"📦 Loading {len(data['categories'])} categories, {len(data['products'])} products, {len(data['variants'])} variants")

# Import Categories
category_map = {}
for cat_data in data['categories']:
    category, created = Category.objects.get_or_create(
        name=cat_data['name'],
        defaults={'slug': cat_data['slug']}
    )
    category_map[cat_data['id']] = category
    if created:
        print(f"  ✅ Created category: {category.name}")

# Import Products with Images
product_map = {}
for prod_data in data['products']:
    category = category_map.get(prod_data['category_id'])
    if not category:
        continue
    
    product, created = Product.objects.get_or_create(
        slug=prod_data['slug'],
        defaults={
            'name': prod_data['name'],
            'description': prod_data['description'],
            'category': category,
            'base_price': prod_data['base_price'],
            'is_active': prod_data.get('is_active', True),
            'featured': prod_data.get('featured', False),
        }
    )
    
    # Handle image
    if prod_data.get('main_image'):
        old_image_path = prod_data['main_image']
        # Extract just the filename
        image_filename = os.path.basename(old_image_path)
        
        # Check if image exists in source folder
        source_path = os.path.join(IMAGE_SOURCE_FOLDER, image_filename)
        
        # Also check if it's already in media/products/
        existing_path = os.path.join(IMAGE_DEST_FOLDER, image_filename)
        
        if os.path.exists(source_path):
            # Copy image to media/products/
            dest_path = os.path.join(IMAGE_DEST_FOLDER, image_filename)
            shutil.copy2(source_path, dest_path)
            print(f"  📸 Copied image: {image_filename}")
            
            # Update product with image
            if created:
                product.main_image = f'products/{image_filename}'
                product.save()
        elif os.path.exists(existing_path):
            # Image already exists in media/products/
            if created:
                product.main_image = f'products/{image_filename}'
                product.save()
            print(f"  📸 Image already exists: {image_filename}")
        else:
            # Image not found - check if it was in the SQLite path
            # Try to find it in the old media folder
            old_media_path = os.path.join('media', old_image_path)
            if os.path.exists(old_media_path):
                dest_path = os.path.join(IMAGE_DEST_FOLDER, image_filename)
                shutil.copy2(old_media_path, dest_path)
                if created:
                    product.main_image = f'products/{image_filename}'
                    product.save()
                print(f"  📸 Found and copied image from old path: {image_filename}")
            else:
                print(f"  ⚠️ Image not found: {image_filename}")
    
    product_map[prod_data['id']] = product
    if created:
        print(f"  ✅ Created product: {product.name}")

# Import Variants
for var_data in data['variants']:
    product = product_map.get(var_data['product_id'])
    if not product:
        continue
    
    variant, created = ProductVariant.objects.get_or_create(
        product=product,
        color=var_data.get('color', ''),
        storage=var_data.get('storage', ''),
        defaults={
            'additional_price': var_data.get('additional_price', 0),
            'sku': var_data.get('sku', ''),
        }
    )
    if created:
        print(f"  ✅ Created variant: {variant}")

print("🎉 Import with images completed!")
print(f"📁 Images should be in: {IMAGE_DEST_FOLDER}")
