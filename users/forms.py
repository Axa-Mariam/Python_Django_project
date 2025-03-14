from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django import forms
from .models import Users, CartItem, Order, PaymentInfo, OrderItem, Product, ProductDiscount, Notification
from datetime import date
import re
from django.core.files.images import get_image_dimensions
from django.utils.text import slugify
from django.utils import timezone

class UserRegistrationForm(UserCreationForm):
    mobile = forms.CharField(
        max_length=15,
        label="Mobile",
        widget=forms.TextInput(attrs={'placeholder': 'Enter your mobile number'})
    )
    
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'})
    )

    class Meta:
        model = Users
        fields = ('username', 'email', 'mobile', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Users.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile')
        if not mobile.isdigit() or len(mobile) < 10:
            raise forms.ValidationError("Please enter a valid mobile number.")
        if Users.objects.filter(mobile=mobile).exists():
            raise forms.ValidationError("This mobile number is already registered.")
        return mobile

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Enter your username', 'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password', 'class': 'form-control'})
    )

class UserProfileUpdateForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    
    mobile = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your mobile number'
        })
    )

    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False
    )
    
    # Add address fields
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter your address'
        }),
        required=False
    )
    
    city = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your city'
        }),
        required=False
    )
    
    country = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your country'
        }),
        required=False
    )
    
    postal_code = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your postal code'
        }),
        required=False
    )

    class Meta:
        model = Users
        fields = ['email', 'mobile', 'date_of_birth', 'gender', 'marital_status', 
                 'blood_group', 'address', 'city', 'country', 'postal_code']
        widgets = {
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'marital_status': forms.Select(attrs={'class': 'form-control'}),
            'blood_group': forms.Select(attrs={'class': 'form-control'})
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Users.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile')
        if not mobile.isdigit() or len(mobile) < 10:
            raise forms.ValidationError("Please enter a valid mobile number.")
        if Users.objects.filter(mobile=mobile).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("This mobile number is already registered.")
        return mobile

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 13:
                raise forms.ValidationError("You must be at least 13 years old to register.")
            if age > 120:
                raise forms.ValidationError("Please enter a valid date of birth.")
        return dob
    
class UserPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes and placeholders
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your current password'
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter new password'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })

# New forms for e-commerce functionality
class CartItemForm(forms.ModelForm):
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control quantity-input',
            'min': '1',
            'value': '1'
        })
    )
    
    class Meta:
        model = CartItem
        fields = ['quantity']
    
    def __init__(self, *args, **kwargs):
        # Store product for validation
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
        
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity < 1:
            raise forms.ValidationError("Quantity must be at least 1.")
        
        # Check against product stock
        product = self.product
        # If product wasn't passed, try to get it from the instance
        if not product and self.instance and self.instance.pk:
            product = self.instance.product
            
        if product and quantity > product.stock:
            raise forms.ValidationError(f"Only {product.stock} items available in stock.")
        
        return quantity

class ShippingAddressForm(forms.Form):
    # Use same address as profile option
    use_profile_address = forms.BooleanField(
        label="Use my profile address",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # Shipping fields
    shipping_address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter shipping address'
        }),
        required=False
    )
    
    shipping_city = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter city'
        }),
        required=False
    )
    
    shipping_country = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter country'
        }),
        required=False
    )
    
    shipping_postal_code = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter postal code'
        }),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        use_profile_address = cleaned_data.get('use_profile_address')
        
        if not use_profile_address:
            # If not using profile address, validate shipping fields
            required_fields = ['shipping_address', 'shipping_city', 'shipping_country', 'shipping_postal_code']
            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, 'This field is required when not using profile address.')
        elif self.user:
            # If using profile address, check if user has complete address information
            if not all([self.user.address, self.user.city, self.user.country, self.user.postal_code]):
                self.add_error(None, 'Your profile address is incomplete. Please fill out the shipping address.')
        
        return cleaned_data

class PaymentMethodForm(forms.Form):
    PAYMENT_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('paypal', 'PayPal'),
        ('cod', 'Cash on Delivery')
    ]
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )

class CreditCardPaymentForm(forms.ModelForm):
    card_number = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Card Number',
            'maxlength': '16'
        }),
        required=True
    )
    
    cardholder_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Cardholder Name'
        }),
        required=True
    )
    
    card_expiry = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'MM/YY',
            'maxlength': '5'
        }),
        required=True
    )
    
    cvv = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'CVV',
            'maxlength': '3'
        }),
        required=True
    )
    
    class Meta:
        model = PaymentInfo
        fields = ['card_number', 'cardholder_name', 'card_expiry', 'cvv']
    
    def clean_card_number(self):
        card_number = self.cleaned_data.get('card_number')
        # Simple validation for demo purposes
        if not card_number.isdigit() or len(card_number) != 16:
            raise forms.ValidationError("Please enter a valid 16-digit card number.")
        return card_number
    
    def clean_card_expiry(self):
        card_expiry = self.cleaned_data.get('card_expiry')
        # Check format MM/YY
        if not re.match(r'^(0[1-9]|1[0-2])\/([0-9]{2})$', card_expiry):
            raise forms.ValidationError("Expiry date must be in MM/YY format.")
        
        # Extract month and year
        month, year = card_expiry.split('/')
        current_year = int(date.today().strftime('%y'))
        current_month = int(date.today().strftime('%m'))
        
        # Convert to integers for comparison
        month = int(month)
        year = int(year)
        
        # Check if card is expired
        if (year < current_year) or (year == current_year and month < current_month):
            raise forms.ValidationError("This card has expired.")
            
        return card_expiry
    
    def clean_cvv(self):
        cvv = self.cleaned_data.get('cvv')
        if not cvv.isdigit() or len(cvv) != 3:
            raise forms.ValidationError("CVV must be a 3-digit number.")
        return cvv

class OrderSearchForm(forms.Form):
    order_id = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Order ID'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All')] + list(Order.STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    def clean_status(self):
        status = self.cleaned_data.get('status')
        if status and status not in dict(Order.STATUS_CHOICES):
            raise forms.ValidationError("Invalid order status selected.")
        return status
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            self.add_error('date_to', 'End date must be after start date.')
        
        return cleaned_data

# New form for Product management
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'brand', 'description', 'features', 
                 'price', 'image', 'stock', 'is_available']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'brand': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'features': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.01', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_image(self):
        image = self.cleaned_data.get('image')
        if not image:
            if not self.instance.pk:  # Only require image for new products
                raise forms.ValidationError("Please upload a product image.")
            return self.instance.image  # Return existing image if editing
        
        # Validate image dimensions
        width, height = get_image_dimensions(image)
        if width < 200 or height < 200:
            raise forms.ValidationError("Image dimensions should be at least 200x200 pixels.")
            
        # Validate file size (max 2MB)
        if image.size > 2 * 1024 * 1024:
            raise forms.ValidationError("Image file size should be less than 2MB.")
            
        return image
        
    def clean_name(self):
        name = self.cleaned_data.get('name')
        # Generate a slug from the name
        slug = slugify(name)
        
        # Check if slug exists (excluding the current instance if editing)
        qs = Product.objects.filter(slug=slug)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
            
        if qs.exists():
            raise forms.ValidationError("A product with a similar name already exists.")
        
        return name
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Generate slug if not already set
        if not instance.slug:
            instance.slug = slugify(instance.name)
            
        if commit:
            instance.save()
            
        return instance

# Form for Product Discounts
class ProductDiscountForm(forms.ModelForm):
    class Meta:
        model = ProductDiscount
        fields = ['product', 'discount_percent', 'valid_from', 'valid_to', 'is_active']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'discount_percent': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.01',
                'max': '99.99',
                'step': '0.01'
            }),
            'valid_from': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'valid_to': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_discount_percent(self):
        discount = self.cleaned_data.get('discount_percent')
        if discount <= 0:
            raise forms.ValidationError("Discount must be greater than 0%.")
        if discount >= 100:
            raise forms.ValidationError("Discount cannot be 100% or more.")
        return discount
    
    def clean_valid_from(self):
        valid_from = self.cleaned_data.get('valid_from')
        # Don't allow dates in the past when creating new discounts
        if not self.instance.pk and valid_from and valid_from < timezone.now():
            raise forms.ValidationError("Start date cannot be in the past.")
        return valid_from
    
    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get('valid_from')
        valid_to = cleaned_data.get('valid_to')
        product = cleaned_data.get('product')
        
        if valid_from and valid_to and valid_from >= valid_to:
            self.add_error('valid_to', 'End date must be after start date.')
        
        # Check for overlapping discounts for the same product
        if product and valid_from and valid_to:
            overlapping = ProductDiscount.objects.filter(
                product=product,
                valid_from__lt=valid_to,
                valid_to__gt=valid_from,
                is_active=True
            )
            
            # Exclude current instance if editing
            if self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)
                
            if overlapping.exists():
                self.add_error(
                    None, 
                    "This discount overlaps with another active discount for the same product. "
                    "Please adjust the dates."
                )
        
        return cleaned_data

# Form for Notifications
class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['user', 'title', 'message', 'notification_type']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notification_type': forms.Select(attrs={'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If editing existing notification, show read status (read-only)
        if self.instance and self.instance.pk:
            self.fields['read'] = forms.BooleanField(
                required=False, 
                disabled=True,
                initial=self.instance.read,
                help_text="This field is automatically updated when a user reads the notification."
            )
            
            # Show read timestamp if applicable
            if self.instance.read_at:
                self.fields['read_at'] = forms.DateTimeField(
                    disabled=True,
                    initial=self.instance.read_at,
                    widget=forms.DateTimeInput(attrs={'class': 'form-control'}),
                    help_text="When the notification was read by the user."
                )