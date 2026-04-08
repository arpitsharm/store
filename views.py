from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from .models import Product, Category, Cart, CartItem, Order, OrderItem, Review, Wishlist, Coupon, CustomerProfile, Address, Complaint
from .forms import UserRegisterForm, UserLoginForm, ReviewForm, OrderForm, CustomerProfileForm, AddressForm, ComplaintForm


# Helper function to get or create cart
def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart


# Home Page
def home_view(request):
    # Remove featured products, show regular products instead
    products = Product.objects.filter(is_available=True)[:8]
    new_arrivals = Product.objects.filter(is_available=True).order_by('-created_at')[:8]
    promoted_products = Product.objects.filter(is_promoted=True, is_available=True)[:8]
    categories = Category.objects.all()[:6]
    
    context = {
        'products': products,
        'new_arrivals': new_arrivals,
        'promoted_products': promoted_products,
        'categories': categories,
    }
    return render(request, 'store/home.html', context)


# About Page
def about_view(request):
    """About page for The Diora"""
    return render(request, 'store/about.html')


# Product Catalog
def product_list_view(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(is_available=True)
    
    # Filter by category
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    # Search functionality
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )
    
    # Price range filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'rating':
        products = products.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'category': category,
        'query': query,
        'sort_by': sort_by,
    }
    return render(request, 'store/product_list.html', context)


# Product Detail
def product_detail_view(request, slug):
    product = get_object_or_404(Product, slug=slug)
    reviews = product.reviews.filter(approved=True)
    related_products = Product.objects.filter(category=product.category, is_available=True).exclude(id=product.id)[:4]
    
    if request.method == 'POST' and request.user.is_authenticated:
        review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.product = product
            review.user = request.user
            review.approved = True  # Auto-approve reviews
            review.save()
            messages.success(request, 'Review submitted successfully!')
            return redirect('product_detail', slug=product.slug)
    else:
        review_form = ReviewForm()
    
    # Get cart info for this product
    cart_item_quantity = 0
    cart_item_id = None
    if request.user.is_authenticated:
        from .models import Cart
        try:
            cart = Cart.objects.get(user=request.user)
            cart_item = cart.items.filter(product=product).first()
            if cart_item:
                cart_item_quantity = cart_item.quantity
                cart_item_id = cart_item.id
        except Cart.DoesNotExist:
            pass
    
    context = {
        'product': product,
        'review_form': review_form,
        'reviews': reviews,
        'related_products': related_products,
        'pending_reviews_count': product.reviews.filter(approved=False).count(),
        'cart_item_quantity': cart_item_quantity,
        'cart_item_id': cart_item_id,
    }
    return render(request, 'store/product_detail.html', context)


# Cart Views
def cart_view(request):
    cart = get_or_create_cart(request)
    cart_items = cart.items.all()
    
    # Coupon code handling
    discount = 0
    coupon_code = request.session.get('coupon_code', None)
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code, is_active=True)
            if coupon.is_valid():
                subtotal = cart.get_subtotal()
                if subtotal >= coupon.min_purchase:
                    if coupon.discount_type == 'percentage':
                        discount = subtotal * (coupon.discount_value / 100)
                    else:
                        discount = coupon.discount_value
        except Coupon.DoesNotExist:
            pass
    
    total = cart.get_subtotal() - discount
    
    context = {
        'cart_items': cart_items,
        'cart': cart,
        'total': total,
        'discount': discount,
    }
    return render(request, 'store/cart.html', context)


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_or_create_cart(request)
    
    # Check if product is available
    if not product.is_available or product.stock_quantity <= 0:
        messages.error(request, f'Sorry, {product.name} is out of stock.')
        return redirect('product_detail', slug=product.slug)
    
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    # Calculate requested quantity
    requested_qty = cart_item.quantity + 1 if not created else 1
    
    # Check if requested quantity exceeds stock
    if requested_qty > product.stock_quantity:
        messages.error(request, f'Cannot add more than {product.stock_quantity} items to cart. Only {product.stock_quantity} available.')
        if created:
            cart_item.delete()
        else:
            return redirect('product_detail', slug=product.slug)
    else:
        if not created:
            cart_item.quantity = requested_qty
            cart_item.save()
        messages.success(request, f'{product.name} added to cart!')
    
    # Redirect back to product detail page (not cart)
    return redirect('product_detail', slug=product.slug)


def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    messages.success(request, 'Item removed from cart.')
    return redirect('cart')


def update_cart_quantity(request, item_id):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart_item = get_object_or_404(CartItem, id=item_id)
        
        # Check stock availability
        if quantity > cart_item.product.stock_quantity:
            messages.error(request, f'Cannot update quantity. Only {cart_item.product.stock_quantity} items available in stock.')
            return redirect('cart')
        
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Cart updated.')
        else:
            cart_item.delete()
            messages.success(request, 'Item removed from cart.')
    return redirect('cart')


def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('coupon_code', '')
        try:
            coupon = Coupon.objects.get(code=code, is_active=True)
            if coupon.is_valid():
                request.session['coupon_code'] = code
                messages.success(request, f'Coupon {code} applied successfully!')
            else:
                messages.error(request, 'Coupon is not valid.')
        except Coupon.DoesNotExist:
            messages.error(request, 'Invalid coupon code.')
    return redirect('cart')


def remove_coupon(request):
    if 'coupon_code' in request.session:
        del request.session['coupon_code']
        messages.success(request, 'Coupon removed.')
    return redirect('cart')


# Checkout Views
@login_required(login_url='/login/')
def checkout_view(request):
    cart = get_or_create_cart(request)
    
    if cart.items.count() == 0:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart')
    
    # Check stock availability for all items in cart
    out_of_stock_items = []
    over_quantity_items = []
    
    for item in cart.items.all():
        if not item.product.is_available or item.product.stock_quantity <= 0:
            out_of_stock_items.append(item.product.name)
        elif item.quantity > item.product.stock_quantity:
            over_quantity_items.append({
                'product': item.product.name,
                'requested': item.quantity,
                'available': item.product.stock_quantity
            })
    
    # If there are out of stock items, show error and redirect
    if out_of_stock_items:
        items_str = ', '.join(out_of_stock_items)
        messages.error(request, f'The following items are now out of stock: {items_str}. Please remove them from your cart.')
        return redirect('cart')
    
    # If any item quantity exceeds stock, show error and redirect
    if over_quantity_items:
        error_msg = 'Some items have insufficient stock: '
        for item_info in over_quantity_items:
            error_msg += f"{item_info['product']} (requested: {item_info['requested']}, available: {item_info['available']}); "
        messages.error(request, error_msg)
        return redirect('cart')
    
    # Get user profile info
    profile = getattr(request.user, 'profile', None)
    
    if request.method == 'POST':
        order_form = OrderForm(request.POST)
        if order_form.is_valid():
            order = order_form.save(commit=False)
            order.user = request.user
            
            # Check if payment method is ONLINE (Paytm)
            if order.payment_method == 'ONLINE':
                messages.error(request, 'Sorry, Paytm payment service is temporarily not available. Please choose Cash on Delivery (COD) or try again later.')
                return redirect('checkout')
            
            # Calculate total
            subtotal = cart.get_subtotal()
            discount = 0
            coupon_code = request.session.get('coupon_code', None)
            if coupon_code:
                try:
                    coupon = Coupon.objects.get(code=coupon_code, is_active=True)
                    if coupon.is_valid() and subtotal >= coupon.min_purchase:
                        if coupon.discount_type == 'percentage':
                            discount = subtotal * (coupon.discount_value / 100)
                        else:
                            discount = coupon.discount_value
                        coupon.used_count += 1
                        coupon.save()
                except Coupon.DoesNotExist:
                    pass
            
            order.total_amount = subtotal - discount
            order.coupon_code = coupon_code
            order.discount_amount = discount
            
            # Generate unique order number with retry logic
            import datetime
            today = datetime.datetime.now()
            date_str = today.strftime('%Y%m%d')
            
            # Get the last order number and increment
            def generate_order_number():
                last_order = Order.objects.filter(order_number__startswith=f'DIORA-{date_str}-').order_by('-order_number').first()
                if last_order:
                    try:
                        last_num = int(last_order.order_number.split('-')[-1])
                        new_num = str(last_num + 1).zfill(4)
                    except (ValueError, IndexError):
                        new_num = '0001'
                else:
                    new_num = '0001'
                return f'DIORA-{date_str}-{new_num}'
            
            # Try to save with unique order number
            max_retries = 5
            for attempt in range(max_retries):
                order.order_number = generate_order_number()
                try:
                    order.save()
                    break
                except Exception as e:
                    if 'UNIQUE constraint failed' in str(e) and attempt < max_retries - 1:
                        continue  # Retry
                    else:
                        raise e
            
            # Create order items and check stock one final time
            stock_issues = []
            for cart_item in cart.items.all():
                # Double-check stock before creating order
                if cart_item.product.stock_quantity < cart_item.quantity:
                    stock_issues.append(f"{cart_item.product.name} (needed: {cart_item.quantity}, available: {cart_item.product.stock_quantity})")
                
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price
                )
                # Update product stock
                cart_item.product.stock_quantity -= cart_item.quantity
                cart_item.product.save()
            
            # If there were stock issues, rollback the order
            if stock_issues:
                order.delete()
                messages.error(request, f'Order could not be placed due to stock issues: {", ".join(stock_issues)}')
                return redirect('cart')
            
            # Clear cart
            cart.items.all().delete()
            if 'coupon_code' in request.session:
                del request.session['coupon_code']
            
            messages.success(request, f'Order placed successfully! Order Number: {order.order_number}')
            
            # If online payment, redirect to Paytm
            if order.payment_method == 'ONLINE':
                return redirect('paytm_payment', order_id=order.id)
            
            # For COD orders, status remains 'pending'
            return redirect('order_detail', order_number=order.order_number)
        else:
            # Form is invalid - show errors
            print("Form errors:", order_form.errors)
            messages.error(request, 'Please fill all required fields correctly. Check the form for errors.')
    else:
        order_form = OrderForm()
    
    # Calculate totals
    discount = 0
    coupon_code = request.session.get('coupon_code', None)
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code, is_active=True)
            if coupon.is_valid():
                subtotal = cart.get_subtotal()
                if subtotal >= coupon.min_purchase:
                    if coupon.discount_type == 'percentage':
                        discount = subtotal * (coupon.discount_value / 100)
                    else:
                        discount = coupon.discount_value
        except Coupon.DoesNotExist:
            pass
    
    total = cart.get_subtotal() - discount
    
    context = {
        'order_form': order_form,
        'cart': cart,
        'subtotal': cart.get_subtotal(),
        'discount': discount,
        'total': total,
        'profile': profile,
    }
    return render(request, 'store/checkout.html', context)


@login_required(login_url='/login/')
def order_detail_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    order_items = order.items.all()
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'store/order_detail.html', context)


@login_required(login_url='/login/')
def order_history_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'store/order_history.html', context)


@login_required(login_url='/login/')
def cancel_order_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.cancel_order():
        messages.success(request, f'Order #{order.order_number} has been cancelled successfully.')
    else:
        messages.error(request, 'This order cannot be cancelled.')
    
    return redirect('order_history')


@login_required(login_url='/login/')
def return_order_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.return_order():
        messages.success(request, f'Order #{order.order_number} has been returned successfully.')
    else:
        messages.error(request, 'This order cannot be returned.')
    
    return redirect('order_history')


# Wishlist Views
@login_required(login_url='/login/')
def wishlist_view(request):
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    context = {
        'wishlist': wishlist,
    }
    return render(request, 'store/wishlist.html', context)


@login_required(login_url='/login/')
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    if product not in wishlist.products.all():
        wishlist.products.add(product)
        messages.success(request, f'{product.name} added to wishlist!')
    else:
        messages.info(request, f'{product.name} is already in your wishlist.')
    
    return redirect('wishlist')


@login_required(login_url='/login/')
def remove_from_wishlist(request, product_id):
    wishlist = get_object_or_404(Wishlist, user=request.user)
    product = get_object_or_404(Product, id=product_id)
    
    if product in wishlist.products.all():
        wishlist.products.remove(product)
        messages.success(request, f'{product.name} removed from wishlist.')
    
    return redirect('wishlist')


# Authentication Views
def register_view(request):
    if request.user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create customer profile
            from .models import CustomerProfile
            CustomerProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, f'Account created for {user.username}!')
            return redirect('/')
    else:
        form = UserRegisterForm()
    
    context = {
        'form': form,
    }
    return render(request, 'store/register.html', context)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            next_url = request.GET.get('next', '/')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    form = UserLoginForm()
    context = {'form': form}
    return render(request, 'store/login.html', context)


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('/')


# User Profile Views
@login_required(login_url='/login/')
def profile_view(request):
    profile, created = CustomerProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        profile_form = CustomerProfileForm(request.POST, request.FILES, instance=profile)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        profile_form = CustomerProfileForm(instance=profile)
    
    context = {
        'profile_form': profile_form,
        'profile': profile,
    }
    return render(request, 'store/profile.html', context)


# Edit Review View (User can edit their own review)
@login_required(login_url='/login/')
def edit_review_view(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    
    # Only allow the review author to edit
    if review.user != request.user:
        messages.error(request, 'You can only edit your own reviews.')
        return redirect('home')
    
    if request.method == 'POST':
        review.rating = request.POST.get('rating')
        review.comment = request.POST.get('comment')
        review.save()
        messages.success(request, 'Review updated successfully!')
        return redirect('product_detail', slug=review.product.slug)
    
    return redirect('product_detail', slug=review.product.slug)


# Address Management Views
@login_required(login_url='/login/')
def address_list_view(request):
    addresses = Address.objects.filter(user=request.user)
    
    if request.method == 'POST' and 'delete_address_id' in request.POST:
        address_id = request.POST.get('delete_address_id')
        address = get_object_or_404(Address, id=address_id, user=request.user)
        address.delete()
        messages.success(request, 'Address deleted successfully!')
        return redirect('address_list')
    
    context = {
        'addresses': addresses,
    }
    return render(request, 'store/address_list.html', context)


@login_required(login_url='/login/')
def add_address_view(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            
            # If this is set as default, unset other defaults
            if address.is_default:
                Address.objects.filter(user=request.user).update(is_default=False)
            
            address.save()
            messages.success(request, 'Address added successfully!')
            return redirect('address_list')
    else:
        form = AddressForm()
    
    context = {
        'form': form,
    }
    return render(request, 'store/address_form.html', context)


@login_required(login_url='/login/')
def edit_address_view(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            new_address = form.save(commit=False)
            
            # If this is set as default, unset other defaults
            if new_address.is_default:
                Address.objects.filter(user=request.user).update(is_default=False)
            
            new_address.save()
            messages.success(request, 'Address updated successfully!')
            return redirect('address_list')
    else:
        form = AddressForm(instance=address)
    
    context = {
        'form': form,
        'address': address,
    }
    return render(request, 'store/address_form.html', context)


@login_required(login_url='/login/')
def set_default_address_view(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    # Set this as default and unset others
    Address.objects.filter(user=request.user).update(is_default=False)
    address.is_default = True
    address.save()
    
    messages.success(request, 'Default address updated!')
    return redirect('address_list')


# Complaint Views
@login_required(login_url='/login/')
def complaint_list_view(request):
    complaints = Complaint.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'complaints': complaints,
    }
    return render(request, 'store/complaint_list.html', context)


@login_required(login_url='/login/')
def create_complaint_view(request):
    order_id = request.GET.get('order')
    initial_data = {}
    if order_id:
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            initial_data['order'] = order
        except Order.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = ComplaintForm(request.user, request.POST, initial=initial_data)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.user = request.user
            complaint.save()
            messages.success(request, 'Complaint submitted successfully! We will respond soon.')
            return redirect('complaint_list')
    else:
        form = ComplaintForm(request.user, initial=initial_data)
    
    context = {
        'form': form,
    }
    return render(request, 'store/complaint_form.html', context)


# Paytm Payment Gateway Views
@login_required(login_url='/login/')
def paytm_payment_view(request, order_id):
    """Display Paytm payment page - redirects to real Paytm gateway"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Check if order is already paid
    if order.payment_method == 'ONLINE' and order.status != 'pending':
        messages.warning(request, 'This order has already been processed.')
        return redirect('order_detail', order_number=order.order_number)
    
    # Import Paytm config
    from .paytm import get_paytm_config, generate_checksum
    
    # Get Paytm configuration
    paytm_config = get_paytm_config()
    
    # Generate unique order ID for Paytm
    paytm_order_id = f"ORDER_{order.id}_{order.order_number}"
    
    # Prepare Paytm parameters
    param_dict = {
        'MID': paytm_config['MID'],
        'ORDER_ID': paytm_order_id,
        'TXN_AMOUNT': str(order.total_amount),
        'CUST_ID': str(request.user.id),
        'INDUSTRY_TYPE_ID': paytm_config['INDUSTRY_TYPE_ID'],
        'WEBSITE': paytm_config['WEBSITE'],
        'CHANNEL_ID': paytm_config['CHANNEL_ID'],
        'CALLBACK_URL': request.build_absolute_uri(f'/payment/paytm/callback/{order.id}/'),
        'EMAIL': request.user.email,
        'MOBILE_NO': order.shipping_phone,
    }
    
    # Generate checksum
    checksum = generate_checksum(param_dict, paytm_config['MERCHANT_KEY'])
    param_dict['CHECKSUMHASH'] = checksum
    
    # Debug logging
    print("="*50)
    print("PAYTM PAYMENT PAGE LOADED:")
    print(f"Order ID: {order.id}")
    print(f"Order Number: {order.order_number}")
    print(f"Amount: {order.total_amount}")
    print(f"Paytm TXN_URL: {paytm_config['TXN_URL']}")
    print(f"Callback URL: {param_dict['CALLBACK_URL']}")
    print("="*50)
    
    context = {
        'order': order,
        'amount': order.total_amount,
        'paytm_config': paytm_config,
        'param_dict': param_dict,
        'paytm_url': paytm_config['TXN_URL'],
    }
    return render(request, 'store/paytm_payment.html', context)


@csrf_exempt
def paytm_callback_view(request, order_id):
    """Handle Paytm payment callback/response"""
    try:
        # Don't require login for Paytm callback (Paytm server posts here)
        # But we still need to verify the order exists
        order = get_object_or_404(Order, id=order_id)
        
        from .paytm import get_paytm_config, verify_checksum
        
        paytm_config = get_paytm_config()
        
        # Get all parameters from POST
        param_dict = {}
        for key, value in request.POST.items():
            param_dict[key] = value
        
        # Debug: Log the response from Paytm
        print("="*50)
        print("PAYTM CALLBACK RESPONSE:")
        for key, value in param_dict.items():
            print(f"{key}: {value}")
        print("="*50)
        
        # Verify checksum
        checksum_hash = param_dict.get('CHECKSUMHASH', '')
        status = param_dict.get('STATUS', '')
        error_msg = param_dict.get('RESPMSG', '')
        
        # Check if we received a checksum
        if not checksum_hash:
            print("WARNING: No CHECKSUMHASH received from Paytm")
        
        # Verify checksum with Paytm
        is_valid_checksum = verify_checksum(param_dict, paytm_config['MERCHANT_KEY'], checksum_hash)
        
        if is_valid_checksum:
            # Check payment status
            if status == 'TXN_SUCCESS':
                # Payment successful - update order
                order.payment_method = 'ONLINE'
                order.status = 'processing'  # Update status to processing after successful payment
                order.save()
                
                # If user is authenticated, show success page
                if request.user.is_authenticated:
                    context = {
                        'order': order,
                        'payment_method_display': 'Paytm Online Payment',
                        'transaction_id': param_dict.get('TXNID', 'N/A'),
                    }
                    return render(request, 'store/payment_success.html', context)
                else:
                    # Redirect to login with success message
                    messages.success(request, f'Payment successful! Order #{order.order_number} is now being processed.')
                    return redirect('login')
            else:
                # Payment FAILED - cancel the order
                print(f"PAYMENT FAILED - Status: {status}, Error: {error_msg}")
                
                # Update order status to cancelled
                order.status = 'cancelled'
                order.notes = f"Payment failed via Paytm. RESPMSG: {error_msg}, RESPCODE: {param_dict.get('RESPCODE', 'N/A')}"
                order.save()
                
                # Restore product stock
                for order_item in order.items.all():
                    if order_item.product:
                        order_item.product.stock_quantity += order_item.quantity
                        order_item.product.save()
                
                if request.user.is_authenticated:
                    context = {
                        'order': order,
                        'payment_method_display': 'Paytm Online Payment',
                        'error_message': error_msg or 'Payment failed',
                    }
                    return render(request, 'store/payment_failed.html', context)
                else:
                    messages.error(request, f'Payment failed: {error_msg or "Unknown error"}. Your order has been cancelled.')
                    return redirect('login')
        else:
            # Invalid checksum - possible tampering
            print(f"CHECKSUM VERIFICATION FAILED - Status: {status}, Error: {error_msg}")
            
            # Show error to user
            if request.user.is_authenticated:
                messages.error(request, f'Payment verification failed: {error_msg}. Please contact support if amount was deducted.')
                return redirect('order_detail', order_number=order.order_number)
            else:
                # For unauthenticated users, redirect to order detail (they can view by order number)
                return redirect('order_detail', order_number=order.order_number)
    
    except Exception as e:
        # Catch any unexpected errors and show user-friendly message
        print(f"ERROR IN PAYTM CALLBACK: {str(e)}")
        import traceback
        traceback.print_exc()
        
        messages.error(request, f'Payment processing error. Please contact support.')
        return redirect('home')


@login_required(login_url='/login/')
def process_paytm_payment(request, order_id):
    """This view is no longer used - keeping for backward compatibility"""
    return redirect('paytm_payment', order_id=order_id)
