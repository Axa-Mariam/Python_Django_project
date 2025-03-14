from django.contrib import admin
from .models import (
    Users, 
    Notification, 
    Category, 
    Product, 
    ProductDiscount, 
    CartItem, 
    Order, 
    OrderItem, 
    PaymentInfo
)
from .utils import create_sample_sports_data

@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'mobile', 'gender', 'city', 'is_active')
    list_filter = ('gender', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'mobile', 'first_name', 'last_name')
    fieldsets = (
        ('Authentication', {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'mobile', 'gender', 
                                     'marital_status', 'date_of_birth', 'blood_group')}),
        ('Address', {'fields': ('address', 'city', 'country', 'postal_code')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'created_at', 'read')
    list_filter = ('notification_type', 'read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    ordering = ('-created_at',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')
    list_filter = ('is_active',)
    actions = ['initialize_sports_data']
    
    def initialize_sports_data(self, request, queryset):
        count = create_sample_sports_data()
        self.message_user(request, f"Successfully created {count} sample sports products.")
    initialize_sports_data.short_description = "Initialize sample sports data"

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'brand', 'price', 'stock', 'is_available')
    list_filter = ('category', 'brand', 'is_available', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description', 'brand', 'features')
    fieldsets = (
        ('Basic Information', {'fields': ('name', 'slug', 'category', 'brand', 'description')}),
        ('Product Details', {'fields': ('features', 'price', 'image')}),
        ('Inventory', {'fields': ('stock', 'is_available')}),
        ('Metadata', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ProductDiscount)
class ProductDiscountAdmin(admin.ModelAdmin):
    list_display = ('product', 'discount_percent', 'valid_from', 'valid_to', 'is_active')
    list_filter = ('is_active', 'valid_from', 'valid_to')

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'product__name')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'status', 'payment_status', 'created_at')
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('user__username', 'id')
    inlines = [OrderItemInline]

@admin.register(PaymentInfo)
class PaymentInfoAdmin(admin.ModelAdmin):
    list_display = ('order', 'transaction_id', 'payment_status', 'payment_date')
    search_fields = ('transaction_id', 'order__id')
    list_filter = ('payment_status',)