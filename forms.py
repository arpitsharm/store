from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Product, Review, Order, CustomerProfile, Coupon, Address, Category, Complaint


class CategoryForm(forms.ModelForm):
    """Form for adding/editing categories"""
    class Meta:
        model = Category
        fields = ['name', 'description', 'image', 'parent']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'parent': forms.Select(attrs={'class': 'form-control'}),
        }


class UserRegisterForm(UserCreationForm):
    """User registration form with additional fields"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Email'})
        self.fields['first_name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'First Name'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Last Name'})
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Username'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})


class UserLoginForm(AuthenticationForm):
    """Custom login form"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Username'})
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})


class ProductForm(forms.ModelForm):
    """Form for adding/editing products (owner use)"""
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock_quantity', 'category', 
                  'images', 'additional_images', 'material', 
                  'is_featured', 'is_available']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'material': forms.TextInput(attrs={'class': 'form-control'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ReviewForm(forms.ModelForm):
    """Form for submitting product reviews"""
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class OrderForm(forms.ModelForm):
    """Checkout order form"""
    class Meta:
        model = Order
        fields = [
            'shipping_first_name', 'shipping_last_name', 'shipping_email', 
            'shipping_phone', 'shipping_address_line1', 'shipping_address_line2',
            'shipping_city', 'shipping_state', 'shipping_zipcode',
            'billing_same_as_shipping', 'payment_method', 'notes'
        ]
        widgets = {
            'shipping_first_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'shipping_last_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'shipping_email': forms.EmailInput(attrs={'class': 'form-control', 'required': True}),
            'shipping_phone': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'shipping_address_line1': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'shipping_address_line2': forms.TextInput(attrs={'class': 'form-control', 'required': False}),
            'shipping_city': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'shipping_state': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'shipping_zipcode': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'billing_same_as_shipping': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'payment_method': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CustomerProfileForm(forms.ModelForm):
    """Form for updating customer profile"""
    class Meta:
        model = CustomerProfile
        fields = ['phone', 'address_line1', 'address_line2', 'city', 'state', 'zipcode', 'profile_picture']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'zipcode': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }


class CouponForm(forms.ModelForm):
    """Form for creating coupons (owner use)"""
    class Meta:
        model = Coupon
        fields = ['code', 'description', 'discount_type', 'discount_value', 
                  'min_purchase', 'valid_from', 'valid_until', 'is_active', 'usage_limit']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'discount_type': forms.Select(attrs={'class': 'form-control'}),
            'discount_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'min_purchase': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valid_from': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'valid_until': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'usage_limit': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class AddressForm(forms.ModelForm):
    """Form for adding/editing customer addresses"""
    class Meta:
        model = Address
        fields = ['label', 'address_line1', 'address_line2', 'city', 'state', 'zipcode', 'phone', 'is_default']
        widgets = {
            'label': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Home, Work'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 1'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 2 (optional)'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'zipcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ZIP Code'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ComplaintForm(forms.ModelForm):
    """Form for submitting complaints about orders"""
    class Meta:
        model = Complaint
        fields = ['order', 'subject', 'description']
        widgets = {
            'order': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief subject of your complaint'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Detailed description of your issue'}),
        }
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show orders belonging to the user
        self.fields['order'].queryset = Order.objects.filter(user=user)
