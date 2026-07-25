from .basket import Basket

def basket_total(request):
    basket = Basket(request)
    return {
        'basket_total': basket.get_total_items(),
        'basket_subtotal': basket.get_total_price(),
        'basket_items': list(basket),
        'basket': basket,
    }