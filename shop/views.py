from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Min, Max, Avg, Sum, Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from datetime import timedelta
from .models import Product, Category, Wishlist, ProductReview
from .forms import ReviewForm
from checkout.models import Order, OrderItem

def home_page(request):
    # Get 8 featured products
    featured_products = Product.objects.filter(is_active=True, featured=True)[:8]
    
    # Get all active product IDs that are NOT in featured
    featured_ids = featured_products.values_list('id', flat=True)
    
    # Get 8 new arrivals that are NOT featured
    new_arrivals = Product.objects.filter(is_active=True).exclude(id__in=featured_ids).order_by('-created_at')[:8]
    
    # If there aren't enough non-featured products, just get the latest 8
    if new_arrivals.count() < 8:
        new_arrivals = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
    
    categories = Category.objects.all()
    
    # Reorder categories for homepage
    category_order = ['Neckbands', 'Smart Watches', 'Earpods']
    ordered_categories = []
    for name in category_order:
        try:
            cat = categories.get(name=name)
            ordered_categories.append(cat)
        except Category.DoesNotExist:
            pass
    for cat in categories:
        if cat.name not in category_order:
            ordered_categories.append(cat)
    
    context = {
        'featured_products': featured_products,
        'categories': ordered_categories,
        'new_arrivals': new_arrivals,
    }
    return render(request, 'shop/home.html', context)
def product_list(request):
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.all()
    
    category_order = ['Neckbands', 'Smart Watches', 'Earpods']
    ordered_categories = []
    for name in category_order:
        try:
            cat = categories.get(name=name)
            ordered_categories.append(cat)
        except Category.DoesNotExist:
            pass
    for cat in categories:
        if cat.name not in category_order:
            ordered_categories.append(cat)
    
    price_range = products.aggregate(min_price=Min('base_price'), max_price=Max('base_price'))
    min_price = float(price_range['min_price'] or 0)
    max_price = float(price_range['max_price'] or 10000)
    
    min_price_filter = request.GET.get('min_price')
    max_price_filter = request.GET.get('max_price')
    if min_price_filter and max_price_filter:
        products = products.filter(base_price__gte=min_price_filter, base_price__lte=max_price_filter)
    
    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    search_query = request.GET.get('q')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )
    
    sort_by = request.GET.get('sort')
    if sort_by == 'price_asc':
        products = products.order_by('base_price')
    elif sort_by == 'price_desc':
        products = products.order_by('-base_price')
    else:
        products = products.order_by('-created_at')
    
    paginator = Paginator(products, 12)
    page = request.GET.get('page', 1)
    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)
    
    context = {
        'products': products_page,
        'categories': ordered_categories,
        'active_category': category_slug,
        'search_query': search_query,
        'sort_by': sort_by,
        'min_price': int(min_price),
        'max_price': int(max_price),
        'selected_min': int(min_price_filter) if min_price_filter else int(min_price),
        'selected_max': int(max_price_filter) if max_price_filter else int(max_price),
    }
    return render(request, 'shop/list.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    variants = product.variants.all()
    related_products = Product.objects.filter(category=product.category, is_active=True).exclude(id=product.id)[:4]
    
    reviews = product.reviews.filter(is_approved=True)
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    user_has_reviewed = request.user.is_authenticated and product.reviews.filter(user=request.user).exists()
    
    context = {
        'product': product,
        'variants': variants,
        'related_products': related_products,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'user_has_reviewed': user_has_reviewed,
        'review_form': ReviewForm(),
    }
    return render(request, 'shop/detail.html', context)

def search_api(request):
    query = request.GET.get('q', '')
    results = []
    if len(query) >= 2:
        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query),
            is_active=True
        )[:10]
        results = [{'name': p.name, 'slug': p.slug, 'price': str(p.base_price)} for p in products]
    return JsonResponse(results, safe=False)

# ===== WISHLIST =====
@login_required
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.delete()
        return JsonResponse({'status': 'removed'})
    return JsonResponse({'status': 'added'})

# ===== PRODUCT REVIEWS =====
@login_required
def add_review(request, slug):
    product = get_object_or_404(Product, slug=slug)
    
    if ProductReview.objects.filter(product=product, user=request.user).exists():
        messages.warning(request, "You've already reviewed this product.")
        return redirect('product_detail', slug=slug)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, "Thanks! Your review is pending approval.")
    return redirect('product_detail', slug=slug)

# ===== ADMIN DASHBOARD =====
@staff_member_required
def dashboard_view(request):
    days = 30
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    orders = Order.objects.filter(
        created_at__gte=start_date,
        payment_status='fully_paid'
    )
    
    total_revenue = orders.aggregate(total=Sum('total_amount'))['total'] or 0
    total_orders = orders.count()
    
    recent_orders = Order.objects.filter(payment_status='fully_paid').order_by('-created_at')[:10]
    
    top_products = OrderItem.objects.filter(
        order__created_at__gte=start_date,
        order__payment_status='fully_paid'
    ).values('product_name').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('price')
    ).order_by('-total_quantity')[:10]
    
    all_orders = Order.objects.filter(created_at__gte=start_date)
    paid = all_orders.filter(payment_status='fully_paid').count()
    pending = all_orders.filter(payment_status='pending').count()
    cancelled = all_orders.filter(payment_status='cancelled').count()
    
    context = {
        'total_revenue': float(total_revenue),
        'total_orders': total_orders,
        'paid_orders': paid,
        'pending_orders': pending,
        'cancelled_orders': cancelled,
        'recent_orders': recent_orders,
        'top_products': top_products,
        'title': 'Dashboard',
    }
    return render(request, 'admin/reports/dashboard.html', context)

# ===== FOOTER PAGE VIEWS =====
def privacy_policy(request):
    return render(request, 'shop/privacy_policy.html')

def terms_of_service(request):
    return render(request, 'shop/terms_of_service.html')

def returns_policy(request):
    return render(request, 'shop/returns_policy.html')

def faq_page(request):
    return render(request, 'shop/faq.html')