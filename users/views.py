from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q, Sum
from django.urls import reverse
from django.conf import settings
import uuid
from decimal import Decimal
from django.utils.text import slugify

from .forms import (
    UserRegistrationForm, UserLoginForm, UserProfileUpdateForm, 
    UserPasswordChangeForm, CartItemForm, ShippingAddressForm,
    PaymentMethodForm, CreditCardPaymentForm, OrderSearchForm,
    ProductForm, ProductDiscountForm, NotificationForm 
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
                title="Welcome to our store!",
                message="Thank you for registering. Start shopping today!",
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
            # Clean and format data before saving
            profile = form.save(commit=False)
            
            # Save the profile
            profile.save()
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
    notifications = request.user.notifications.all().order_by('-created_at')  # Get all notifications
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
    
    context = {
        'featured_products': featured_products,
        'categories': categories,
        'discounted_products': discounted_products,
        'new_arrivals': new_arrivals,
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
    form = CartItemForm()
    
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
    sort_by = request.GET.get('sort', 'default')
    
    if category_id:
        products = products.filter(category_id=category_id)
        
    if brand:
        products = products.filter(brand=brand)
        
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
    
    context = {
        'products': products,
        'categories': categories,
        'brands': brands,
        'selected_category': category_id,
        'selected_brand': brand,
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
                
            messages.success(request, "Product added to your cart!")
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
        form = CartItemForm(request.POST, instance=cart_item)
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
def cart(request):
    """Display the user's cart"""
    cart_items = CartItem.objects.filter(user=request.user)
    cart_total = sum(item.get_total() for item in cart_items)
    
    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
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
    
    # Calculate cart total
    cart_total = sum(item.get_total() for item in cart_items)
    
    if request.method == 'POST':
        shipping_form = ShippingAddressForm(request.POST, user=request.user)
        payment_form = PaymentMethodForm(request.POST)
        
        if shipping_form.is_valid() and payment_form.is_valid():
            # Get shipping details
            use_profile_address = shipping_form.cleaned_data.get('use_profile_address')
            
            if use_profile_address:
                # Use address from user profile
                shipping_address = request.user.address
                shipping_city = request.user.city
                shipping_country = request.user.country
                shipping_postal_code = request.user.postal_code
            else:
                # Use provided shipping address
                shipping_address = shipping_form.cleaned_data.get('shipping_address')
                shipping_city = shipping_form.cleaned_data.get('shipping_city')
                shipping_country = shipping_form.cleaned_data.get('shipping_country')
                shipping_postal_code = shipping_form.cleaned_data.get('shipping_postal_code')
            
            # Get payment method
            payment_method = payment_form.cleaned_data.get('payment_method')
            
            # Create order
            order = Order.objects.create(
                user=request.user,
                total_amount=cart_total,
                payment_method=payment_method,
                shipping_address=shipping_address,
                shipping_city=shipping_city,
                shipping_country=shipping_country,
                shipping_postal_code=shipping_postal_code,
            )
            
            # Create order items
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    price=cart_item.product.get_discount_price(),
                    quantity=cart_item.quantity
                )
                
                # Update product stock
                product = cart_item.product
                product.stock -= cart_item.quantity
                if product.stock <= 0:
                    product.is_available = False
                product.save()
            
            # Store order ID in session for payment processing
            request.session['order_id'] = order.id
            
            # Clear the cart after order creation
            cart_items.delete()
            
            # If payment method is COD, mark as pending and redirect to confirmation
            if payment_method == 'cod':
                order.status = 'processing'
                order.save()
                create_notification(
                    user=request.user,
                    title="Order Placed Successfully",
                    message=f"Your order #{order.id} has been placed successfully. Payment will be collected on delivery.",
                    notification_type='success'
                )
                messages.success(request, 'Your order has been placed successfully!')
                return redirect('users:order_confirmation', order_id=order.id)
            else:
                # Redirect to payment page for card/PayPal
                return redirect('users:payment', payment_method=payment_method)
    else:
        shipping_form = ShippingAddressForm(user=request.user)
        payment_form = PaymentMethodForm()
    
    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'shipping_form': shipping_form,
        'payment_form': payment_form,
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
                payment = form.save(commit=False)
                payment.order = order
                
                # Generate a fake transaction ID
                payment.transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
                payment.payment_status = True
                payment.save()
                
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
                
                # Clear session
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
        # Demo PayPal integration
        # In a real application, this would redirect to PayPal
        # For this demo, we'll simulate a successful PayPal payment
        
        # Create payment record
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
    
    else:
        messages.error(request, 'Invalid payment method.')
        return redirect('users:checkout')

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

@login_required
def manage_products(request):
    """Admin view to manage products"""
    # Check if user is staff/admin
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('users:dashboard')
    
    products = Product.objects.all()
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Product added successfully!")
            return redirect('users:manage_products')
    else:
        form = ProductForm()
    
    return render(request, 'users/manage_products.html', {
        'products': products,
        'form': form
    })

@login_required
def edit_product(request, product_id):
    """Admin view to edit a product"""
    # Check if user is staff/admin
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('users:dashboard')
    
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully!")
            return redirect('users:manage_products')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'users/edit_product.html', {
        'form': form,
        'product': product
    })