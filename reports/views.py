from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from checkout.models import Order, OrderItem

@staff_member_required
def dashboard(request):
    """Admin dashboard view - staff only"""
    return render(request, 'reports/dashboard.html')

@staff_member_required
def api_sales_summary(request):
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    orders = Order.objects.filter(
        created_at__gte=start_date,
        payment_status='fully_paid'
    )
    
    total_revenue = orders.aggregate(total=Sum('total_amount'))['total'] or 0
    total_orders = orders.count()
    average_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    daily_sales = []
    for i in range(days):
        day = end_date - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        day_orders = orders.filter(created_at__range=(day_start, day_end))
        day_revenue = day_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        daily_sales.append({
            'day': day.strftime('%Y-%m-%d'),
            'revenue': float(day_revenue),
            'orders': day_orders.count()
        })
    
    return JsonResponse({
        'total_revenue': float(total_revenue),
        'total_orders': total_orders,
        'average_order_value': float(average_order_value),
        'daily_sales': daily_sales[::-1],
    })

@staff_member_required
def api_top_products(request):
    days = int(request.GET.get('days', 30))
    limit = int(request.GET.get('limit', 10))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    top_products = OrderItem.objects.filter(
        order__created_at__gte=start_date,
        order__payment_status='fully_paid'
    ).values('product_name').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('price')
    ).order_by('-total_quantity')[:limit]
    
    result = []
    for item in top_products:
        result.append({
            'product_name': item['product_name'],
            'total_quantity': item['total_quantity'],
            'total_revenue': float(item['total_revenue'])
        })
    
    return JsonResponse(result, safe=False)

@staff_member_required
def api_payment_stats(request):
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    orders = Order.objects.filter(created_at__gte=start_date)
    total = orders.count()
    paid = orders.filter(payment_status='fully_paid').count()
    pending = orders.filter(payment_status='pending').count()
    cancelled = orders.filter(payment_status='cancelled').count()
    
    return JsonResponse({
        'total': total,
        'paid': paid,
        'pending': pending,
        'cancelled': cancelled,
        'success_rate': round(paid / total * 100, 2) if total > 0 else 0,
    })

@staff_member_required
def api_category_sales(request):
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    category_sales = OrderItem.objects.filter(
        order__created_at__gte=start_date,
        order__payment_status='fully_paid'
    ).values('variant__product__category__name').annotate(
        total_revenue=Sum('price')
    ).order_by('-total_revenue')
    
    result = []
    for item in category_sales:
        name = item['variant__product__category__name'] or 'Uncategorized'
        result.append({
            'category': name,
            'revenue': float(item['total_revenue'] or 0)
        })
    
    return JsonResponse(result, safe=False)

@staff_member_required
def api_delivery_stats(request):
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    delivery_stats = Order.objects.filter(
        created_at__gte=start_date,
        payment_status='fully_paid'
    ).values('delivery_location').annotate(
        orders=Count('id'),
        revenue=Sum('total_amount')
    ).order_by('-orders')
    
    result = []
    for item in delivery_stats:
        result.append({
            'location': item['delivery_location'] or 'Unknown',
            'orders': item['orders'],
            'revenue': float(item['revenue'] or 0)
        })
    
    return JsonResponse(result, safe=False)

@staff_member_required
def api_recent_orders(request):
    limit = int(request.GET.get('limit', 10))
    orders = Order.objects.filter(payment_status='fully_paid').order_by('-created_at')[:limit]
    
    result = []
    for order in orders:
        result.append({
            'order_id': order.order_id,
            'customer_name': order.customer_name,
            'customer_phone': order.customer_phone,
            'total_amount': float(order.total_amount),
            'status': order.payment_status,
            'created_at': order.created_at.isoformat(),
        })
    
    return JsonResponse(result, safe=False)
