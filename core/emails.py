from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_order_confirmation_email(order):
    """
    Send order confirmation email to customer
    """
    try:
        subject = f"✅ Order Confirmation - #{order.order_id}"
        
        # Build context
        context = {
            'order': order,
            'customer_name': order.customer_name,
            'order_id': order.order_id,
            'total': order.total_amount,
            'subtotal': order.subtotal,
            'delivery_fee': order.delivery_fee,
            'items': order.items.all(),
            'delivery_location': order.delivery_location,
            'delivery_address': order.delivery_address,
            'delivery_notes': order.delivery_notes,
            'payment_status': order.get_payment_status_display(),
            'delivery_status': order.get_delivery_status_display(),
            'created_at': order.created_at,
            'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'https://oraimotechhub.co.ke',
        }
        
        # Try to render HTML template, fallback to plain text
        try:
            html_message = render_to_string('emails/order_confirmation.html', context)
        except Exception:
            html_message = None
        
        # Plain text fallback
        try:
            plain_message = render_to_string('emails/order_confirmation.txt', context)
        except Exception:
            plain_message = f"""
Order Confirmation - #{order.order_id}

Hello {order.customer_name},

Thank you for your order!

Order #: {order.order_id}
Total: KES {order.total_amount}
Delivery: {order.delivery_location}

We'll notify you once your order ships.

Questions? WhatsApp us at 254715804141.

Oraimo Tech Hub
"""
        
        if html_message:
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[order.customer_email],
                reply_to=[settings.DEFAULT_FROM_EMAIL],
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)
        else:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.customer_email],
                fail_silently=False,
            )
        
        logger.info(f"Order confirmation email sent for {order.order_id} to {order.customer_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send order confirmation email: {str(e)}")
        return False


def send_payment_collected_email(order):
    """
    Send payment collected notification to customer
    """
    try:
        subject = f"💰 Payment Collected - Order #{order.order_id}"
        
        context = {
            'order': order,
            'customer_name': order.customer_name,
            'order_id': order.order_id,
            'total': order.total_amount,
            'collected_at': order.cod_collected_at,
            'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'https://oraimotechhub.co.ke',
        }
        
        plain_message = f"""
Payment Collected - Order #{order.order_id}

Hello {order.customer_name},

Your payment of KES {order.total_amount} for Order #{order.order_id} has been collected.

Thank you for your purchase!

Track your order: {context['site_url']}/checkout/track/{order.order_id}/

Questions? WhatsApp us at 254715804141.

Oraimo Tech Hub
"""
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.customer_email],
            fail_silently=False,
        )
        
        logger.info(f"Payment collected email sent for {order.order_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send payment collected email: {str(e)}")
        return False


def send_order_shipped_email(order):
    """
    Send order shipped notification to customer
    """
    try:
        subject = f"🚚 Your Order #{order.order_id} Has Been Shipped!"
        
        context = {
            'order': order,
            'customer_name': order.customer_name,
            'order_id': order.order_id,
            'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'https://oraimotechhub.co.ke',
        }
        
        plain_message = f"""
Order Shipped! - #{order.order_id}

Hello {order.customer_name},

Great news! Your order #{order.order_id} is on the way!

Track your order: {context['site_url']}/checkout/track/{order.order_id}/

Expected delivery: within 2 business days.

Questions? WhatsApp us at 254715804141.

Oraimo Tech Hub
"""
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.customer_email],
            fail_silently=False,
        )
        
        logger.info(f"Order shipped email sent for {order.order_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send order shipped email: {str(e)}")
        return False


def send_admin_order_notification(order):
    """
    Send order notification to admin
    """
    try:
        subject = f"🛒 NEW ORDER - #{order.order_id}"
        
        items_list = ""
        for item in order.items.all():
            items_list += f"  • {item.product_name} × {item.quantity} = KES {item.total}\n"
        
        message = f"""
🛒 NEW ORDER RECEIVED!
===========================================

Order #: {order.order_id}
Customer: {order.customer_name}
Phone: {order.customer_phone}
Email: {order.customer_email}
Date: {order.created_at.strftime('%b %d, %Y %H:%M')}

Total: KES {order.total_amount}
Payment: {order.get_payment_status_display()}

Items:
{items_list}
Delivery Location: {order.delivery_location}
Delivery Address: {order.delivery_address}
{'Delivery Notes: ' + order.delivery_notes if order.delivery_notes else ''}

Admin Link: {settings.SITE_URL if hasattr(settings, 'SITE_URL') else ''}/adteddymin/checkout/order/{order.id}/change/

===========================================
Action Required: Process this order.
"""
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            fail_silently=False,
        )
        
        logger.info(f"Admin notification sent for {order.order_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send admin notification: {str(e)}")
        return False


def send_welcome_email(user):
    """
    Send welcome email to new user
    """
    try:
        subject = "🎉 Welcome to Oraimo Tech Hub!"
        
        site_url = settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'https://oraimotechhub.co.ke'
        
        plain_message = f"""
🎉 Welcome to Oraimo Tech Hub!

Hello {user.username},

Thank you for joining Oraimo Tech Hub!

You now have access to:
✅ Track your orders
✅ Save your delivery addresses
✅ Get exclusive offers

Start shopping at: {site_url}

Questions? Reply to this email or WhatsApp us at 254715804141.

Best regards,
Oraimo Tech Hub Team
"""
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        logger.info(f"Welcome email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send welcome email: {str(e)}")
        return False


def send_test_email(to_email):
    """
    Send a test email to verify email configuration
    """
    try:
        subject = "🔧 Oraimo Tech Hub - Test Email"
        message = """
Hello,

This is a test email from Oraimo Tech Hub.

Your email configuration is working correctly!

Best regards,
Oraimo Tech Hub Team
"""
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=False,
        )
        
        logger.info(f"Test email sent to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send test email: {str(e)}")
        return False