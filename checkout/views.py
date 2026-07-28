from datetime import timezone
from venv import logger

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import FileResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.conf import settings
import uuid
import json
from decimal import Decimal

from basket.basket import Basket
from .models import Order, OrderItem
from .forms import CheckoutForm
from core.emails import (
    send_order_confirmation_email,
    send_admin_order_notification,
    send_payment_collected_email,
    send_order_shipped_email
)
from shop.models import Coupon, UsedCoupon
from notifications import send_console_notification
from receipts import generate_receipt_pdf


def checkout_page(request):
    basket = Basket(request)
    
    if len(basket) == 0:
        messages.warning(request, 'Your basket is empty.')
        return redirect('product_list')
    
    subtotal = float(basket.get_total_price())
    basket_total_items = basket.get_total_items()
    delivery_locations = settings.DELIVERY_FEES
    free_threshold = settings.FREE_DELIVERY_THRESHOLD
    
    # Get coupon from session if applied
    coupon_code = request.session.get('coupon_code', '')
    coupon_discount = request.session.get('coupon_discount', 0)
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        
        if form.is_valid():
            # Get cleaned data
            customer_name = form.cleaned_data['customer_name']
            customer_phone = form.cleaned_data['customer_phone']
            customer_email = form.cleaned_data['customer_email']
            delivery_location = form.cleaned_data['delivery_location']
            delivery_address = form.cleaned_data['delivery_address']
            marketing_consent = form.cleaned_data['marketing_consent']
            delivery_notes = form.cleaned_data.get('delivery_notes', '')
            is_cbd = form.cleaned_data['is_cbd']
            
            # Validate delivery_location is not empty
            if not delivery_location or delivery_location == '':
                messages.error(request, 'Please select a delivery location.')
                return redirect('checkout_page')
            
            # ===== DELIVERY FEE CALCULATION =====
            is_cbd = (delivery_location == 'Nairobi CBD')
            base_fee = delivery_locations.get(delivery_location, 250)
            
            if is_cbd:
                delivery_fee = 0
            elif subtotal >= free_threshold and delivery_location in settings.FREE_OVER_THRESHOLD_LOCATIONS:
                delivery_fee = 0
            else:
                delivery_fee = base_fee
            
            total = subtotal + delivery_fee
            
            # ===== APPLY COUPON DISCOUNT =====
            coupon_applied = None
            coupon_discount_amount = 0
            coupon_code_used = ''
            
            if coupon_code:
                try:
                    coupon = Coupon.objects.get(code=coupon_code.upper(), is_active=True)
                    is_valid, message = coupon.is_valid(total)
                    if is_valid:
                        coupon_discount_amount = coupon.calculate_discount(total)
                        total = total - coupon_discount_amount
                        coupon_applied = coupon
                        coupon_code_used = coupon.code
                        
                        # Mark coupon as used
                        coupon.used_count += 1
                        coupon.save()
                        
                        # Clear session
                        del request.session['coupon_code']
                        del request.session['coupon_discount']
                    else:
                        messages.warning(request, f'Coupon issue: {message}')
                except Coupon.DoesNotExist:
                    messages.warning(request, 'Invalid coupon code.')
            
            # Generate order ID
            order_id = f"OR-{uuid.uuid4().hex[:8].upper()}"
            
            # Create order
            order = Order.objects.create(
                order_id=order_id,
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_email=customer_email,
                delivery_location=delivery_location,
                delivery_address=delivery_address,
                delivery_fee=delivery_fee,
                subtotal=subtotal,
                total_amount=total,
                is_cbd=is_cbd,
                delivery_notes=delivery_notes,
                marketing_consent=marketing_consent,
                payment_status='pending',
                delivery_status='pending',
                coupon=coupon_applied,
                coupon_discount=coupon_discount_amount,
                coupon_code_used=coupon_code_used,
            )
            
            # Create order items
            for item in basket:
                OrderItem.objects.create(
                    order=order,
                    variant_id=item['variant_id'],
                    product_name=item['name'],
                    variant_name=item['name'],
                    quantity=item['quantity'],
                    price=item['price']
                )
            
            # Clear basket
            basket.clear()
            
            # Record coupon usage
            if coupon_applied and coupon_discount_amount > 0:
                UsedCoupon.objects.create(
                    coupon=coupon_applied,
                    user=request.user if request.user.is_authenticated else None,
                    order=order,
                    discount_amount=coupon_discount_amount,
                    order_total=total
                )
            
            # ===== SEND EMAILS =====
            if customer_email:
                try:
                    send_order_confirmation_email(order)
                except Exception as e:
                    logger.error(f"Failed to send confirmation email: {str(e)}")
            
            try:
                send_admin_order_notification(order)
            except Exception as e:
                logger.error(f"Failed to send admin notification: {str(e)}")
            
            send_console_notification(order)
            
            # Show success message
            discount_message = ""
            if coupon_discount_amount > 0:
                discount_message = f" 🎫 You saved KES {coupon_discount_amount:,.2f} with coupon!"
            
            messages.success(
                request, 
                f'🎉 Order {order_id} placed successfully! '
                f'Pay KES {total:,.2f} on delivery.{discount_message}'
            )
            
            return redirect('checkout:order_success', order_id=order_id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {
                'customer_name': request.user.get_full_name() or request.user.username,
                'customer_email': request.user.email,
            }
        form = CheckoutForm(initial=initial)
    
    context = {
        'basket': basket,
        'basket_total': basket_total_items,
        'basket_subtotal': subtotal,
        'subtotal': subtotal,
        'delivery_locations': delivery_locations,
        'free_threshold': free_threshold,
        'form': form,
        'coupon_code': coupon_code,
        'coupon_discount': coupon_discount,
    }
    return render(request, 'checkout/checkout.html', context)


def order_success(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    return render(request, 'checkout/success.html', {'order': order})


def track_order(request, order_id=None):
    order = None
    if order_id:
        order = get_object_or_404(Order, order_id=order_id)
    elif request.GET.get('order_id'):
        try:
            order = Order.objects.get(order_id=request.GET.get('order_id'))
        except Order.DoesNotExist:
            messages.warning(request, 'Order not found. Please check your order ID.')
    
    return render(request, 'checkout/track.html', {'order': order})


def payment_status(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    return render(request, 'checkout/payment_status.html', {'order': order})


def download_receipt(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    pdf_buffer = generate_receipt_pdf(order)
    
    response = FileResponse(
        pdf_buffer,
        as_attachment=True,
        filename=f"receipt_{order.order_id}.pdf",
        content_type='application/pdf'
    )
    return response


# ===== COUPON VIEWS =====

def apply_coupon(request):
    """
    AJAX endpoint to apply a coupon
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    try:
        data = json.loads(request.body)
        coupon_code = data.get('code', '').upper().strip()
        
        if not coupon_code:
            return JsonResponse({
                'success': False,
                'message': 'Please enter a coupon code.'
            })
        
        if len(coupon_code) != 9:
            return JsonResponse({
                'success': False,
                'message': 'Coupon code must be exactly 9 characters.'
            })
        
        # Get basket and calculate total
        basket = Basket(request)
        total = float(basket.get_total_price())
        
        # Get coupon
        try:
            coupon = Coupon.objects.get(code=coupon_code, is_active=True)
        except Coupon.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid coupon code. Please check and try again.'
            })
        
        # Check validity
        is_valid, message = coupon.is_valid(total)
        if not is_valid:
            return JsonResponse({
                'success': False,
                'message': message
            })
        
        # Calculate discount
        discount = float(coupon.calculate_discount(total))
        new_total = total - discount
        
        # Store in session
        request.session['coupon_code'] = coupon_code
        request.session['coupon_discount'] = discount
        
        return JsonResponse({
            'success': True,
            'message': f'✅ Coupon applied! You saved KES {discount:,.2f}',
            'discount': discount,
            'new_total': new_total,
            'percent': coupon.discount_percent,
            'code': coupon_code
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request format.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error applying coupon. Please try again.'
        })


def remove_coupon(request):
    """
    Remove coupon from session
    """
    if 'coupon_code' in request.session:
        del request.session['coupon_code']
    if 'coupon_discount' in request.session:
        del request.session['coupon_discount']
    
    return JsonResponse({
        'success': True,
        'message': 'Coupon removed successfully.'
    })


@login_required
@require_POST
def admin_mark_paid(request, order_id):
    """Admin view to mark payment as collected and send email"""
    order = get_object_or_404(Order, order_id=order_id)
    
    if order.payment_status == 'pending':
        order.payment_status = 'collected'
        order.amount_paid = order.total_amount
        order.remaining_balance = 0
        order.cod_collected_at = timezone.now()
        order.cod_collected_by = request.user
        order.save()
        
        send_payment_collected_email(order)
        
        messages.success(request, f'Payment for {order.order_id} marked as collected. Email sent to customer.')
    else:
        messages.warning(request, f'Payment for {order.order_id} is already {order.payment_status}.')
    
    return redirect('admin:checkout_order_changelist')