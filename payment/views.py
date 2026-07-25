import json
import logging
import hmac
import hashlib
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.urls import reverse
from .models import PaymentTransaction
from .pesapal import PesapalClient
from checkout.models import Order
from notifications import send_order_notification

logger = logging.getLogger(__name__)

def verify_pesapal_signature(request):
    """Signature verification - disabled for COD"""
    return False  # Always return False since Pesapal is disabled

@csrf_exempt
def pesapal_ipn(request):
    """
    Pesapal IPN endpoint - DISABLED for COD mode.
    Redirects to home with a message.
    """
    logger.info("Pesapal IPN called but Pesapal is disabled (COD mode)")
    return JsonResponse({
        'status': 'disabled',
        'message': 'Pesapal is disabled. Payment on Delivery (COD) mode is active.'
    }, status=200)

@csrf_exempt
def pesapal_callback(request):
    """
    Pesapal Callback endpoint - DISABLED for COD mode.
    Redirects to home with a message.
    """
    logger.info("Pesapal Callback called but Pesapal is disabled (COD mode)")
    messages.info(request, 'Payment on Delivery mode is active. No online payment required.')
    return redirect(reverse('shop:home'))

# ===== OPTIONAL: Keep these for future use if you re-enable Pesapal =====
# def verify_pesapal_signature_original(request):
#     """Original signature verification - kept for reference"""
#     signature = request.headers.get('X-Pesapal-Signature')
#     if not signature:
#         logger.warning("No signature header received")
#         return False
#     
#     secret = settings.PESAPAL_CONSUMER_SECRET or settings.SECRET_KEY
#     expected = hmac.new(
#         secret.encode(),
#         request.body,
#         hashlib.sha256
#     ).hexdigest()
#     
#     return hmac.compare_digest(signature, expected)
