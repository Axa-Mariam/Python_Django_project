from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django import forms
from .models import Users, CartItem, Order, PaymentInfo, OrderItem, Notification
from datetime import date
import re
from django.utils import timezone

class UserRegistrationForm(UserCreationForm):
    mobile = forms.CharField(
        max_length=15,
        label="Mobile",
        widget=forms.TextInput(attrs={'placeholder': 'Enter your mobile number', 'class': 'form-control'})
    )
    
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email', 'class': 'form-control'})
    )

    class Meta:
        model = Users
        fields = ('username', 'email', 'mobile', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your username'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm password'})

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
    
    # Address fields
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
        fields = ['email', 'mobile', 'date_of_birth', 'gender', 'address', 'city', 'country', 'postal_code']
        widgets = {
            'gender': forms.Select(attrs={'class': 'form-control'})
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

# E-commerce forms
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
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
        
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity < 1:
            raise forms.ValidationError("Quantity must be at least 1.")
        
        product = self.product
        if not product and self.instance and self.instance.pk:
            product = self.instance.product
            
        if product and quantity > product.stock:
            raise forms.ValidationError(f"Only {product.stock} items available in stock.")
        
        return quantity

class ShippingAddressForm(forms.Form):
    use_profile_address = forms.BooleanField(
        label="Use my profile address",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
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
        
        # Only default to profile address if user has a complete address
        if self.user and all([self.user.address, self.user.city, self.user.country, self.user.postal_code]):
            self.fields['use_profile_address'].initial = True
        else:
            self.fields['use_profile_address'].initial = False
    
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
        fields = ['card_number', 'cardholder_name', 'card_expiry']
    
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

# Simple notification form for customer service
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