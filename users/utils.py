from .models import Notification, Category, Product
from django.utils.text import slugify
from django.utils import timezone
from django.core.files.base import ContentFile
import random
import os
from django.conf import settings 

def create_notification(user, title, message, notification_type='info'):
    """Create a new notification for a user"""
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        created_at=timezone.now()
    )
    return notification

def create_sample_sports_data():
    """Create sample sports categories and products"""
    
    # Create default categories
    categories = {}
    for category_data in Category.get_default_categories():
        category, created = Category.objects.get_or_create(
            name=category_data['name'],
            defaults={
                'slug': slugify(category_data['name']),
                'description': category_data['description'],
                'is_active': True
            }
        )
        categories[category.name] = category
    
    # Sample products data with image information
    sample_products = [
        {
            "name": "Professional Basketball",
            "category": "Team Sports",
            "brand": "wilson",
            "description": "Official size and weight basketball for professional play.",
            "features": "- Official size 7\n- Composite leather cover\n- Deep channel design for better grip\n- Indoor/outdoor use",
            "price": 39.99,
            "stock": 50,
            "image_name": "basketball.jpg"  # Default image filename
        },
        {
            "name": "Adjustable Dumbbell Set",
            "category": "Fitness",
            "brand": "reebok",
            "description": "Versatile dumbbell set with adjustable weights from 5 to 25 pounds.",
            "features": "- Adjustable from 5-25 lbs\n- Space-saving design\n- Durable construction\n- Comfortable grip",
            "price": 149.99,
            "stock": 25,
            "image_name": "dumbbell.jpg"  # Default image filename
        },
        {
            "name": "Running Shoes Premium",
            "category": "Running",
            "brand": "nike",
            "description": "Lightweight running shoes with responsive cushioning for road running.",
            "features": "- Breathable mesh upper\n- Responsive foam midsole\n- Durable rubber outsole\n- Reflective details",
            "price": 129.99,
            "stock": 75,
            "image_name": "shoes.jpg"  # Default image filename
        },
        {
            "name": "Competition Swim Goggles",
            "category": "Swimming",
            "brand": "speedo",
            "description": "Anti-fog swim goggles with UV protection and leak-proof design.",
            "features": "- Anti-fog coating\n- UV protection\n- Adjustable nose bridge\n- Silicone strap",
            "price": 29.99,
            "stock": 100,
            "image_name": "goggles.jpg"  # Default image filename
        },
        {
            "name": "Hiking Backpack 40L",
            "category": "Outdoor Sports",
            "brand": "other",
            "description": "Durable 40L hiking backpack with multiple compartments and rain cover.",
            "features": "- 40L capacity\n- Padded shoulder straps\n- Hydration compatible\n- Integrated rain cover",
            "price": 89.99,
            "stock": 30,
            "image_name": "backpack.jpg"  # Default image filename
        }
    ]
    
    # Create products with default images
    for product_data in sample_products:
        category = categories.get(product_data["category"])
        if category:
            # Check if product exists
            try:
                product = Product.objects.get(name=product_data["name"])
                created = False
            except Product.DoesNotExist:
                # Create with default image
                product = Product(
                    name=product_data["name"],
                    slug=slugify(product_data["name"]),
                    category=category,
                    brand=product_data["brand"],
                    description=product_data["description"],
                    features=product_data["features"],
                    price=product_data["price"],
                    stock=product_data["stock"],
                    is_available=True
                )
                
                # Handle image - use a placeholder if no image is provided
                # This assumes you have a static/placeholder.jpg file in your media directory
                from django.core.files import File
                placeholder_path = os.path.join(settings.MEDIA_ROOT, 'placeholder.jpg')
                if os.path.exists(placeholder_path):
                    with open(placeholder_path, 'rb') as img_file:
                        product.image.save(product_data.get("image_name", "product.jpg"), File(img_file), save=False)
                
                product.save()
                created = True
    
    return len(sample_products)