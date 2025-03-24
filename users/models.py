from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify
from datetime import date
from django.utils import timezone
from decimal import Decimal

class Users(AbstractUser):
    # Simplified choices
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other')
    ]
    
    email = models.EmailField(unique=True, error_messages={'unique': "This email is already registered."})
    mobile = models.CharField(max_length=15, unique=True, error_messages={'unique': "This mobile number is already registered."})
    
    # Personal information (only keep what's relevant for shipping/accounts)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Address information - essential for shipping
    address = models.TextField(max_length=500, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    
    def __str__(self):
        return self.username
    
    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - \
                   ((today.month, today.day) < \
                   (self.date_of_birth.month, self.date_of_birth.day))
        return None
    
    def get_cart_count(self):
        return CartItem.objects.filter(user=self).count()
    
    def get_cart_total(self):
        cart_items = CartItem.objects.filter(user=self)
        return sum(item.get_total() for item in cart_items)


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]

    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=100)
    message = models.TextField()
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES, default='info')
    created_at = models.DateTimeField(default=timezone.now)
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        if not self.read:
            self.read = True
            self.read_at = timezone.now()
            self.save()


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        
    @classmethod
    def get_default_categories(cls):
        """Returns default sports equipment categories"""
        default_categories = [
            {"name": "Team Sports", "description": "Equipment for team sports like football, basketball, and volleyball"},
            {"name": "Fitness", "description": "Weights, exercise mats, and other fitness equipment"},
            {"name": "Running", "description": "Running shoes, apparel, and accessories"},
            {"name": "Swimming", "description": "Swimwear, goggles, and swimming accessories"},
            {"name": "Outdoor Sports", "description": "Equipment for hiking, camping, and outdoor activities"},
            {"name": "Winter Sports", "description": "Skiing, snowboarding, and other winter sports equipment"},
            {"name": "Combat Sports", "description": "Boxing gloves, protective gear, and training equipment"},
            {"name": "Racquet Sports", "description": "Tennis, badminton, and squash equipment"},
        ]
        return default_categories


class Product(models.Model):
    BRAND_CHOICES = [
        ('nike', 'Nike'),
        ('adidas', 'Adidas'),
        ('puma', 'Puma'),
        ('reebok', 'Reebok'),
        ('under_armour', 'Under Armour'),
        ('new_balance', 'New Balance'),
        ('wilson', 'Wilson'),
        ('speedo', 'Speedo'),
        ('other', 'Other')
    ]
    
    # Added size and color options for sports equipment
    SIZE_CATEGORIES = [
        ('XS', 'Extra Small'),
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
        ('XXL', 'Double Extra Large'),
        ('NA', 'Not Applicable')
    ]
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.CharField(max_length=20, choices=BRAND_CHOICES, default='other')
    description = models.TextField()
    features = models.TextField(blank=True, help_text="Key product features and specifications")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/')
    stock = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    size = models.CharField(max_length=3, choices=SIZE_CATEGORIES, default='NA')
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Weight in kg")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    wishlisted_by = models.ManyToManyField(Users, related_name='wishlisted_items', blank=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def is_in_stock(self):
        return self.stock > 0

    def get_discount_price(self):
        """Get discounted price if there's an active discount"""
        discounts = self.discounts.filter(
            is_active=True,
            valid_from__lte=timezone.now(),
            valid_to__gte=timezone.now()
        ).order_by('-discount_percent').first()
        
        if discounts:
            discount_amount = (self.price * discounts.discount_percent) / 100
            return self.price - discount_amount
        return self.price


class ProductDiscount(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='discounts')
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.product.name} - {self.discount_percent}% off"


class CartItem(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'product')
    
    def __str__(self):
        return f"{self.user.username}'s cart: {self.product.name} x {self.quantity}"
    
    def get_total(self):
        return self.product.get_discount_price() * self.quantity


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_CHOICES = [
        ('cod', 'Cash On Delivery'),
        ('card', 'Credit/Debit Card'),
        ('paypal', 'PayPal'),
    ]
    
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='orders')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    payment_status = models.BooleanField(default=False)
    
    # Shipping details
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_country = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)
    tracking_number = models.CharField(max_length=50, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order {self.id} - {self.user.username} ({self.status})"
    
    class Meta:
        ordering = ['-created_at']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at the time of purchase
    quantity = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f"{self.product.name} ({self.quantity}) in Order {self.order.id}"
    
    def get_total(self):
        return self.price * self.quantity


class PaymentInfo(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    
    # For demo payment gateway (minimal fields)
    card_number = models.CharField(max_length=16, blank=True, null=True)
    card_expiry = models.CharField(max_length=7, blank=True, null=True)
    cardholder_name = models.CharField(max_length=100, blank=True, null=True)
    payment_status = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Payment for Order {self.order.id}"