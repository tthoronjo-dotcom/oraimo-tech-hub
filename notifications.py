from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_order_notification(order):
    try:
        subject = f"🛒 New Order: {order.order_id}"
        
        message = f"""
        New Order Received!
        
        Order Details:
        ---------------
        Order ID: {order.order_id}
        Customer: {order.customer_name}
        Phone: {order.customer_phone}
        Email: {order.customer_email or 'Not provided'}
        Location: {order.delivery_location}
        Address: {order.delivery_address}
        Total: KES {order.total_amount}
        Payment Status: {order.payment_status}
        Delivery Status: {order.delivery_status}
        
        Items Ordered:
        """
        
        for item in order.items.all():
            message += f"  • {item.product_name} x {item.quantity} = KES {item.total}\n"
        
        message += f"""
        
        View in Admin: http://127.0.0.1:8000/admin/checkout/order/{order.id}/change/
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL],
            fail_silently=False,
        )
        
        print(f"✅ Email sent for order {order.order_id}")
        return True
        
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False

def send_console_notification(order):
    print("\n" + "="*60)
    print("🛒 NEW ORDER RECEIVED!")
    print("="*60)
    print(f"📦 Order ID:   {order.order_id}")
    print(f"👤 Customer:   {order.customer_name}")
    print(f"📞 Phone:      {order.customer_phone}")
    print(f"📧 Email:      {order.customer_email or 'Not provided'}")
    print(f"📍 Location:   {order.delivery_location}")
    print(f"💰 Total:      KES {order.total_amount}")
    print(f"📋 Status:     {order.payment_status}")
    print("-"*60)
    print("Items:")
    for item in order.items.all():
        print(f"  • {item.product_name} x {item.quantity} = KES {item.total}")
    print("="*60 + "\n")
    return True
