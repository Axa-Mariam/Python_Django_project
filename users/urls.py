from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    # Authentication routes
    path("register/", views.userRegister, name="register"),
    path("login/", views.userLogin, name="login"),
    path("logout/", views.userLogout, name="logout"),

    # User dashboard routes
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profileUpdate/", views.profileUpdate, name="profileUpdate"),
    path('passwordUpdate/', views.passwordUpdate, name='passwordUpdate'),

    # Notification routes
    path('notifications/', views.notificationPanel, name='notifications'),
    path('notifications/mark-read/<int:notification_id>/', views.markNotificationRead, name='markNotificationRead'),
    path('notifications/mark-all-read/', views.markAllNotificationsRead, name='markAllNotificationsRead'),
    path('notifications/count/', views.getNotificationsCount, name='getNotificationsCount'),
    
    # E-commerce routes - Product browsing
    path('', views.home, name='home'),
    path('products/', views.productList, name='product_list'),
    path('filter-products/', views.filterProducts, name='filter_products'),
    path('category/<slug:category_slug>/', views.productList, name='product_list_by_category'),
    path('product/<slug:product_slug>/', views.productDetail, name='product_detail'),
    path('search/', views.search, name='search'),
    
    # Cart routes
    path('cart/', views.cart, name='cart'),
    path('add-to-cart/<int:product_id>/', views.addToCart, name='add_to_cart'),
    path('remove-from-cart/<int:cart_item_id>/', views.removeFromCart, name='remove_from_cart'),
    path('update-cart/<int:cart_item_id>/', views.updateCart, name='update_cart'),
    path('update-cart-ajax/', views.updateCartAjax, name='update_cart_ajax'),
    
    # Checkout and order routes
    path('checkout/', views.checkout, name='checkout'),
    path('payment/<str:payment_method>/', views.payment, name='payment'),
    path('order-confirmation/<int:order_id>/', views.orderConfirmation, name='order_confirmation'),
    path('order-history/', views.orderHistory, name='order_history'),
    path('order-detail/<int:order_id>/', views.orderDetail, name='order_detail'),
    path('order/<int:order_id>/cancel/', views.cancelOrder, name='cancel_order'),
    
    # Wishlist routes
    path('wishlist/', views.wishlist, name='wishlist'),
    path('toggle-wishlist/<int:product_id>/', views.toggleWishlist, name='toggle_wishlist'),
]