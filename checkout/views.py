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
            
            # ===== SEND EMAILS =====
            # Send confirmation to customer
            if customer_email:
                try:
                    send_order_confirmation_email(order)
                    logger.info(f"Order confirmation email sent to {customer_email}")
                except Exception as e:
                    logger.error(f"Failed to send confirmation email: {str(e)}")
            
            # Send notification to admin
            try:
                send_admin_order_notification(order)
                logger.info(f"Admin notification sent for {order.order_id}")
            except Exception as e:
                logger.error(f"Failed to send admin notification: {str(e)}")
            
            # Send console notification
            send_console_notification(order)
            
            # Show success message
            messages.success(
                request, 
                f'🎉 Order {order_id} placed successfully! '
                f'Pay KES {total:,.2f} on delivery. '
                f'📧 A confirmation email has been sent to {customer_email}.'
            )
            
            return redirect('checkout:order_success', order_id=order_id)
        else:
            # Form has errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    
    else:
        # GET request - pre-populate form for logged-in users
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
