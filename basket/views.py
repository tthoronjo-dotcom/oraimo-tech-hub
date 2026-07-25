from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from .basket import Basket
from shop.models import ProductVariant

def basket_detail(request):
    basket = Basket(request)
    return render(request, 'basket/detail.html', {'basket': basket})

@require_POST
def basket_add(request, variant_id):
    basket = Basket(request)
    variant = get_object_or_404(ProductVariant, id=variant_id)
    quantity = int(request.POST.get('quantity', 1))
    basket.add(variant_id, quantity)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'total_items': basket.get_total_items(),
            'total_price': float(basket.get_total_price()),
        })
    return redirect('basket_detail')

@csrf_exempt
@require_POST
def basket_update(request, variant_id):
    try:
        basket = Basket(request)
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 0))
        
        if quantity < 1:
            basket.remove(variant_id)
        else:
            basket.update_quantity(variant_id, quantity)
        
        return JsonResponse({
            'success': True,
            'subtotal': float(basket.get_total_price()),
            'total_items': basket.get_total_items(),
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@require_POST
def basket_remove(request, variant_id):
    basket = Basket(request)
    basket.remove(variant_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'total_items': basket.get_total_items(),
        })
    return redirect('basket_detail')
