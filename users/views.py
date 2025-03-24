from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q
from django.urls import reverse
from django.conf import settings
import uuid
from decimal import Decimal
from django.utils.text import slugify
import json

from .forms import (
    UserRegistrationForm, UserLoginForm, UserProfileUpdateForm, 
    UserPasswordChangeForm, CartItemForm, ShippingAddressForm,
    PaymentMethodForm, CreditCardPaymentForm, OrderSearchForm,
    NotificationForm
)
from .models import (
    Notification, Product, Category, CartItem, Order,
    OrderItem, PaymentInfo, ProductDiscount, Users
)
from .utils import create_notification


def userRegister(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            create_notification(
                user=user,
                title="Welcome to our Sports Store!",
                message="Thank you for registering. Start shopping for your sports equipment today!",
                notification_type='info'
            )
            return redirect('users:dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})

def userLogin(request):
    if request.user.is_authenticated:
        return redirect('users:dashboard')
        
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back {username}!')
                return redirect('users:dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()
    return render(request, 'users/login.html', {'form': form})

@login_required
def userLogout(request):
    logout(request)
    messages.info(request, 'You have successfully logged out.')
    return redirect('users:login')

@login_required
def dashboard(request):
    user = request.user
    context = {
        'user': user,
    }
    
    # Add age to context if date of birth exists
    if user.date_of_birth:
        context['age'] = user.age()
    
    # Add recent orders
    recent_orders = user.orders.all()[:3]
    context['recent_orders'] = recent_orders
    
    # Add cart count
    context['cart_count'] = user.get_cart_count()
    
    context['unread_notifications_count'] = user.notifications.filter(read=False).count()
    
    return render(request, 'users/dashboard.html', context)

@login_required
def passwordUpdate(request):
    if request.method == 'POST':
        form = UserPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Update session to prevent user from being logged out
            update_session_auth_hash(request, user)
            create_notification(
                user=request.user,
                title="Password Updated",
                message="Your password has been successfully changed.",
                notification_type='success'
            )
            messages.success(request, 'Your password was successfully updated!')
            return redirect('users:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserPasswordChangeForm(request.user)
    
    return render(request, 'users/passwordUpdate.html', {'form': form})

@login_required
def profileUpdate(request):
    user = request.user
    
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=user)
        if form.is_valid():
            profile = form.save()
            create_notification(
                user=request.user,
                title="Profile Updated",
                message="Your profile has been successfully updated.",
                notification_type='success'
            )    
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('users:dashboard')
        else:
            # If form is not valid, show error message
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileUpdateForm(instance=user)
    
    context = {
        'form': form,
        'user': user
    }
    
    # Add age to context if date of birth exists
    if user.date_of_birth:
        context['age'] = user.age()
    
    return render(request, 'users/profileUpdate.html', context)

@login_required
def notificationPanel(request):
    notifications = request.user.notifications.all().order_by('-created_at')
    unread_count = request.user.notifications.filter(read=False).count()
    return render(request, 'users/notificationPanel.html', {
        'notifications': notifications,
        'unread_count': unread_count
    })

@login_required
def markNotificationRead(request, notification_id):
    if request.method == 'POST':
        try:
            notification = get_object_or_404(Notification, id=notification_id, user=request.user)
            notification.mark_as_read()
            unread_count = request.user.notifications.filter(read=False).count()
            return JsonResponse({
                'status': 'success',
                'message': 'Notification marked as read',
                'count': unread_count
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=400)

@login_required
def markAllNotificationsRead(request):
    if request.method == 'POST':
        try:
            request.user.notifications.filter(read=False).update(
                read=True,
                read_at=timezone.now()
            )
            return JsonResponse({
                'status': 'success',
                'message': 'All notifications marked as read',
                'count': 0
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=400)

@login_required
def getNotificationsCount(request):
    try:
        count = request.user.notifications.filter(read=False).count()
        return JsonResponse({
            'status': 'success',
            'count': count
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

# E-commerce views
def home(request):
    """Home page with featured sports equipment and categories"""
    featured_products = Product.objects.filter(is_available=True).order_by('-created_at')[:8]
    categories = Category.objects.filter(is_active=True)
    
    # Get products with active discounts for promotions section
    discounted_products = Product.objects.filter(
        is_available=True,
        discounts__is_active=True,
        discounts__valid_from__lte=timezone.now(),
        discounts__valid_to__gte=timezone.now()
    ).distinct()[:4]
    
    # Get newest arrivals
    new_arrivals = Product.objects.filter(is_available=True).order_by('-created_at')[:4]
    
    # Get brand choices for brands section
    product_brands = Product.BRAND_CHOICES
    
    context = {
        'featured_products': featured_products,
        'categories': categories,
        'discounted_products': discounted_products,
        'new_arrivals': new_arrivals,
        'product_brands': product_brands,
        'page_title': 'Sports Equipment Store',
    }
    
    return render(request, 'users/home.html', context)

def productList(request, category_slug=None):
    """List all products or products by category"""
    category = None
    products = Product.objects.filter(is_available=True)
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    context = {
        'products': products,
        'category': category,
        'categories': Category.objects.filter(is_active=True),
    }
    
    return render(request, 'users/product_list.html', context)

def productDetail(request, product_slug):
    """Display detailed sports product information"""
    product = get_object_or_404(Product, slug=product_slug, is_available=True)
    
    # Get active discount if any
    active_discount = ProductDiscount.objects.filter(
        product=product,
        is_active=True,
        valid_from__lte=timezone.now(),
        valid_to__gte=timezone.now()
    ).order_by('-discount_percent').first()
    
    # Get related products from same category
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    
    # Get products from the same brand
    similar_brand_products = Product.objects.filter(
        brand=product.brand
    ).exclude(id=product.id)[:4]
    
    # Form for adding to cart
    form = CartItemForm(product=product)
    
    context = {
        'product': product,
        'related_products': related_products,
        'similar_brand_products': similar_brand_products,
        'form': form,
        'active_discount': active_discount,
        'page_title': product.name
    }
    
    return render(request, 'users/product_detail.html', context)

def filterProducts(request):
    """Filter sports products based on multiple criteria"""
    products = Product.objects.filter(is_available=True)
    categories = Category.objects.filter(is_active=True)
    
    # Apply filters
    category_id = request.GET.get('category')
    brand = request.GET.get('brand')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    size = request.GET.get('size')
    sort_by = request.GET.get('sort', 'default')
    
    if category_id:
        products = products.filter(category_id=category_id)
        
    if brand:
        products = products.filter(brand=brand)
    
    if size:
        products = products.filter(size=size)
        
    if min_price:
        products = products.filter(price__gte=min_price)
        
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Sorting
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'name':
        products = products.order_by('name')
    
    brands = Product.BRAND_CHOICES
    sizes = Product.SIZE_CATEGORIES
    
    context = {
        'products': products,
        'categories': categories,
        'brands': brands,
        'sizes': sizes,
        'selected_category': category_id,
        'selected_brand': brand,
        'selected_size': size,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
        'page_title': 'Sports Equipment Catalog'
    }
    
    return render(request, 'users/filter_products.html', context)

@login_required
def addToCart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = CartItemForm(request.POST, product=product)
        if form.is_valid():
            cart_item, created = CartItem.objects.get_or_create(
                user=request.user,
                product=product,
                defaults={'quantity': form.cleaned_data['quantity']}
            )
            
            if not created:
                cart_item.quantity += form.cleaned_data['quantity']
                cart_item.save()
                
            messages.success(request, f"{product.name} added to your cart!")
            return redirect('users:cart')
    else:
        form = CartItemForm(product=product)
        
    return render(request, 'users/product_detail.html', {
        'product': product,
        'form': form
    })

@login_required
def removeFromCart(request, cart_item_id):
    """Remove an item from the user's cart"""
    cart_item = get_object_or_404(CartItem, id=cart_item_id, user=request.user)
    product_name = cart_item.product.name
    cart_item.delete()
    messages.success(request, f'Removed {product_name} from your cart.')
    return redirect('users:cart')

@login_required
def updateCart(request, cart_item_id):
    """Update the quantity of an item in the user's cart"""
    cart_item = get_object_or_404(CartItem, id=cart_item_id, user=request.user)
    
    if request.method == 'POST':
        form = CartItemForm(request.POST, instance=cart_item, product=cart_item.product)
        if form.is_valid():
            # Check if quantity is within stock limits
            quantity = form.cleaned_data['quantity']
            if quantity > cart_item.product.stock:
                messages.error(request, f'Sorry, only {cart_item.product.stock} units are available.')
            else:
                form.save()
                messages.success(request, 'Cart updated successfully.')
    
    return redirect('users:cart')

@login_required
def updateCartAjax(request):
    """Update cart item quantity via AJAX and return updated totals"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cart_item_id = data.get('cart_item_id')
            quantity = data.get('quantity')
            
            # Validation
            if not cart_item_id or not quantity:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Missing cart item ID or quantity'
                }, status=400)
            
            # Convert to integers
            cart_item_id = int(cart_item_id)
            quantity = int(quantity)
            
            # Get cart item
            cart_item = get_object_or_404(CartItem, id=cart_item_id, user=request.user)
            
            # Check stock
            if quantity > cart_item.product.stock:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Only {cart_item.product.stock} items available'
                }, status=400)
            
            # Update quantity
            cart_item.quantity = quantity
            cart_item.save()
            
            # Calculate new totals
            item_total = cart_item.get_total()
            cart_items = CartItem.objects.filter(user=request.user)
            cart_subtotal = sum(item.get_total() for item in cart_items)
            tax_amount = cart_subtotal * Decimal('0.08')
            shipping_cost = Decimal('5.00')
            grand_total = cart_subtotal + tax_amount + shipping_cost
            
            # Return updated values
            return JsonResponse({
                'status': 'success',
                'message': 'Cart updated successfully',
                'item_total': str(item_total),
                'cart_subtotal': str(cart_subtotal),
                'tax_amount': str(tax_amount.quantize(Decimal('0.01'))),
                'shipping_cost': str(shipping_cost),
                'grand_total': str(grand_total.quantize(Decimal('0.01')))
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=400)

@login_required
def cart(request):
    """Display and manage shopping cart"""
    cart_items = CartItem.objects.filter(user=request.user)
    
    # Calculate totals
    cart_subtotal = sum(item.get_total() for item in cart_items)
    tax_amount = cart_subtotal * Decimal('0.08')
    shipping_cost = Decimal('5.00')
    grand_total = cart_subtotal + tax_amount + shipping_cost
    
    context = {
        'cart_items': cart_items,
        'cart_subtotal': cart_subtotal,
        'tax_amount': tax_amount,
        'shipping_cost': shipping_cost,
        'grand_total': grand_total,
    }
    
    return render(request, 'users/cart.html', context)

@login_required
def checkout(request):
    """Process checkout and collect shipping information"""
    cart_items = CartItem.objects.filter(user=request.user)
    
    # If cart is empty, redirect to cart page
    if not cart_items.exists():
        messages.error(request, 'Your cart is empty.')
        return redirect('users:cart')
    
    # Calculate cart total from database
    cart_subtotal = sum(item.get_total() for item in cart_items)
    tax_amount = cart_subtotal * Decimal('0.08')
    shipping_cost = Decimal('5.00')
    grand_total = cart_subtotal + tax_amount + shipping_cost
    
    if request.method == 'POST':
        # Get shipping details
        use_profile_address = request.POST.get('use_profile_address') == 'True'
        
        if use_profile_address:
            # Use address from user profile
            shipping_address = request.user.address
            shipping_city = request.user.city
            shipping_country = request.user.country
            shipping_postal_code = request.user.postal_code
        else:
            # Use provided shipping address
            shipping_address = request.POST.get('shipping_address')
            shipping_city = request.POST.get('shipping_city')
            shipping_country = request.POST.get('shipping_country')
            shipping_postal_code = request.POST.get('shipping_postal_code')
            
            # Basic validation
            if not shipping_address or not shipping_city or not shipping_country or not shipping_postal_code:
                messages.error(request, 'Please complete all shipping address fields')
                return redirect('users:checkout')
        
        # Get payment method
        payment_method = request.POST.get('payment_method')
        
        # Create order - Now with all needed fields
        order = Order.objects.create(
            user=request.user,
            subtotal=cart_subtotal,
            tax_amount=tax_amount,
            shipping_cost=shipping_cost,
            total_amount=grand_total,
            payment_method=payment_method,
            shipping_address=shipping_address,
            shipping_city=shipping_city,
            shipping_country=shipping_country,
            shipping_postal_code=shipping_postal_code,
            status='pending'
        )
        
        # Create order items
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                price=cart_item.product.get_discount_price(),
                quantity=cart_item.quantity,
                total=cart_item.get_total()
            )
            
            # Update product stock
            product = cart_item.product
            product.stock -= cart_item.quantity
            if product.stock <= 0:
                product.is_available = False
            product.save()
        
        # Process based on payment method
        if payment_method == 'cod':
            order.status = 'processing'
            order.save()
            create_notification(
                user=request.user,
                title="Order Placed Successfully",
                message=f"Your order #{order.id} has been placed successfully. Payment will be collected on delivery.",
                notification_type='success'
            )
        elif payment_method == 'card':
            card_number = request.POST.get('card_number', '')
            card_holder_name = request.POST.get('card_holder_name', '')
            
            # Simple validation
            if not card_number or not card_holder_name:
                messages.error(request, 'Please complete all card details')
                return redirect('users:checkout')
            
            # Create payment record
            PaymentInfo.objects.create(
                order=order,
                transaction_id=f"TXN-{order.id}-{timezone.now().strftime('%Y%m%d')}",
                card_number=card_number[-4:],  # Store last 4 digits only
                cardholder_name=card_holder_name,
                payment_status=True
            )
            
            # Update order status
            order.payment_status = True
            order.status = 'processing'
            order.save()
            
            create_notification(
                user=request.user,
                title="Payment Successful",
                message=f"Payment for order #{order.id} has been processed successfully.",
                notification_type='success'
            )
        
        # Clear the cart after order creation
        cart_items.delete()
        
        messages.success(request, 'Your order has been placed successfully!')
        return redirect('users:order_confirmation', order_id=order.id)
    
    context = {
        'cart_items': cart_items,
        'cart_subtotal': cart_subtotal,
        'tax_amount': tax_amount,
        'shipping_cost': shipping_cost,
        'grand_total': grand_total,
    }
    
    return render(request, 'users/checkout.html', context)

@login_required
def payment(request, payment_method):
    """Process payment for an order"""
    # Get order from session
    order_id = request.session.get('order_id')
    if not order_id:
        messages.error(request, 'No order to process.')
        return redirect('users:dashboard')
    
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if payment_method == 'card':
        if request.method == 'POST':
            form = CreditCardPaymentForm(request.POST)
            if form.is_valid():
                # Process credit card payment (demo only)
                payment = PaymentInfo.objects.create(
                    order=order,
                    transaction_id=f"TXN-{uuid.uuid4().hex[:12].upper()}",
                    card_number=form.cleaned_data.get('card_number')[-4:],  # Store last 4 digits only
                    card_holder_name=form.cleaned_data.get('card_holder_name'),
                    payment_status=True
                )
                
                # Update order status
                order.payment_status = True
                order.status = 'processing'
                order.save()
                
                create_notification(
                    user=request.user,
                    title="Payment Successful",
                    message=f"Payment for order #{order.id} has been processed successfully.",
                    notification_type='success'
                )
                
                messages.success(request, 'Payment processed successfully!')
                
                # Clear cart and session
                if 'order_id' in request.session:
                    del request.session['order_id']
                
                return redirect('users:order_confirmation', order_id=order.id)
        else:
            form = CreditCardPaymentForm()
        
        context = {
            'form': form,
            'order': order,
        }
        
        return render(request, 'users/payment_card.html', context)
    
    elif payment_method == 'paypal':
        # Demo PayPal integration - immediately process as successful
        payment = PaymentInfo.objects.create(
            order=order,
            transaction_id=f"PP-{uuid.uuid4().hex[:10].upper()}",
            payment_status=True
        )
        
        # Update order status
        order.payment_status = True
        order.status = 'processing'
        order.save()
        
        create_notification(
            user=request.user,
            title="PayPal Payment Successful",
            message=f"Payment for order #{order.id} has been processed successfully via PayPal.",
            notification_type='success'
        )
        
        messages.success(request, 'PayPal payment processed successfully!')
        
        # Clear session
        if 'order_id' in request.session:
            del request.session['order_id']
        
        return redirect('users:order_confirmation', order_id=order.id)
    
    else:  # cod (Cash on Delivery)
        order.status = 'processing'
        order.save()
        
        create_notification(
            user=request.user,
            title="Order Placed Successfully",
            message=f"Your order #{order.id} has been placed successfully. Payment will be collected on delivery.",
            notification_type='success'
        )
        
        # Clear session
        if 'order_id' in request.session:
            del request.session['order_id']
        
        return redirect('users:order_confirmation', order_id=order.id)

@login_required
def orderConfirmation(request, order_id):
    """Display order confirmation after successful checkout"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.all()
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    
    return render(request, 'users/order_confirmation.html', context)

@login_required
def orderHistory(request):
    """Display the user's order history"""
    form = OrderSearchForm(request.GET or None)
    orders = Order.objects.filter(user=request.user)
    
    if form.is_valid():
        # Apply filters if provided
        if form.cleaned_data.get('order_id'):
            orders = orders.filter(id=form.cleaned_data.get('order_id'))
        if form.cleaned_data.get('status'):
            orders = orders.filter(status=form.cleaned_data.get('status'))
        if form.cleaned_data.get('date_from'):
            orders = orders.filter(created_at__gte=form.cleaned_data.get('date_from'))
        if form.cleaned_data.get('date_to'):
            orders = orders.filter(created_at__lte=form.cleaned_data.get('date_to'))
    
    context = {
        'orders': orders,
        'form': form,
    }
    
    return render(request, 'users/order_history.html', context)

@login_required
def orderDetail(request, order_id):
    """Display detailed information about a specific order"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.all()
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    
    return render(request, 'users/order_detail.html', context)

@login_required
def cancelOrder(request, order_id):
    """Cancel an order"""
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        # Only allow cancellation if order is not delivered or already canceled
        if order.status in ['pending', 'processing', 'shipped']:
            # Update order status
            order.status = 'cancelled'
            order.save()
            
            # Return items to stock
            order_items = order.items.all()
            for item in order_items:
                product = item.product
                product.stock += item.quantity
                product.is_available = True
                product.save()
            
            create_notification(
                user=request.user,
                title="Order Cancelled",
                message=f"Your order #{order.id} has been cancelled successfully.",
                notification_type='info'
            )
            
            messages.info(request, f'Order #{order.id} has been cancelled successfully.')
        else:
            messages.error(request, 'This order cannot be cancelled.')
    
    return redirect('users:order_detail', order_id=order_id)

@login_required
def toggleWishlist(request, product_id):
    """Add or remove a product from the user's wishlist"""
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        user = request.user
        
        if user in product.wishlisted_by.all():
            # Remove from wishlist
            product.wishlisted_by.remove(user)
            wishlisted = False
            message = f"Removed {product.name} from your wishlist."
        else:
            # Add to wishlist
            product.wishlisted_by.add(user)
            wishlisted = True
            message = f"Added {product.name} to your wishlist."
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'wishlisted': wishlisted,
                'message': message
            })
        else:
            messages.success(request, message)
            return redirect('users:product_detail', product_slug=product.slug)
    
    return redirect('users:product_list')

@login_required
def wishlist(request):
    """Display the user's wishlist"""
    wishlisted_products = request.user.wishlisted_items.all()
    
    context = {
        'wishlisted_products': wishlisted_products,
    }
    
    return render(request, 'users/wishlist.html', context)

def search(request):
    """Search for products by name or description"""
    query = request.GET.get('q', '')
    products = []
    
    if query:
        products = Product.objects.filter(
            (Q(name__icontains=query) | Q(description__icontains=query)) &
            Q(is_available=True)
        )
    
    context = {
        'query': query,
        'products': products,
    }
    
    return render(request, 'users/search_results.html', context)