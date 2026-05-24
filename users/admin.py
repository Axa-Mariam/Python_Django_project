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

@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'mobile', 'gender', 'city', 'is_active', 'age')
    list_filter = ('gender', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'mobile', 'first_name', 'last_name')
    readonly_fields = ('last_login', 'date_joined')
    fieldsets = (
        ('Authentication', {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'mobile', 'gender', 
                                     'date_of_birth')}),
        ('Address', {'fields': ('address', 'city', 'country', 'postal_code')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'created_at', 'read')
    list_filter = ('notification_type', 'read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    readonly_fields = ('created_at', 'read_at')
    ordering = ('-created_at',)
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        for notification in queryset:
            notification.mark_as_read()
        self.message_user(request, f"Successfully marked {queryset.count()} notifications as read.")
    mark_as_read.short_description = "Mark selected notifications as read"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(read=False, read_at=None)
        self.message_user(request, f"Successfully marked {updated} notifications as unread.")
    mark_as_unread.short_description = "Mark selected notifications as unread"

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    list_editable = ('is_active',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')
    list_filter = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    actions = ['initialize_sports_data']
    

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'brand', 'price', 'stock', 'is_available', 'size')
    list_filter = ('category', 'brand', 'is_available', 'created_at', 'size')
    list_editable = ('price', 'stock', 'is_available')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description', 'brand', 'features')
    fieldsets = (
        ('Basic Information', {'fields': ('name', 'slug', 'category', 'brand', 'description')}),
        ('Product Details', {'fields': ('features', 'price', 'image', 'size', 'weight')}),
        ('Inventory', {'fields': ('stock', 'is_available')}),
        ('Metadata', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('wishlisted_by',)

@admin.register(ProductDiscount)
class ProductDiscountAdmin(admin.ModelAdmin):
    list_display = ('product', 'discount_percent', 'valid_from', 'valid_to', 'is_active')
    list_filter = ('is_active', 'valid_from', 'valid_to')
    list_editable = ('discount_percent', 'is_active')
    search_fields = ('product__name',)
    actions = ['activate_discounts', 'deactivate_discounts']
    
    def activate_discounts(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Successfully activated {updated} discounts.")
    activate_discounts.short_description = "Activate selected discounts"
    
    def deactivate_discounts(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Successfully deactivated {updated} discounts.")
    deactivate_discounts.short_description = "Deactivate selected discounts"

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'get_total', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'product__name')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_total(self, obj):
        return f"${obj.get_total()}"
    get_total.short_description = 'Total Price'

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('get_total',)
    
    def get_total(self, obj):
        return f"${obj.get_total()}"
    get_total.short_description = 'Total'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'status', 'payment_status', 'created_at')
    list_filter = ('status', 'payment_status', 'created_at', 'payment_method')
    list_editable = ('status',)
    search_fields = ('user__username', 'id', 'tracking_number')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [OrderItemInline]
    actions = ['mark_as_shipped', 'mark_as_delivered']
    
    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status='shipped')
        self.message_user(request, f"Successfully marked {updated} orders as shipped.")
    mark_as_shipped.short_description = "Mark selected orders as shipped"
    
    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(status='delivered')
        self.message_user(request, f"Successfully marked {updated} orders as delivered.")
    mark_as_delivered.short_description = "Mark selected orders as delivered"

@admin.register(PaymentInfo)
class PaymentInfoAdmin(admin.ModelAdmin):
    list_display = ['order', 'transaction_id', 'payment_status', 'payment_date', 'cardholder_name']  # Fix here
    search_fields = ['order__id', 'transaction_id', 'cardholder_name']  # Fix here
    list_filter = ['payment_status', 'payment_date']
    readonly_fields = ('payment_date',)
    
    # For security reasons, let's mask the card number in the admin
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ('card_number', 'card_expiry')
        return self.readonly_fields