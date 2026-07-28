from django.urls import path
from . import views

app_name = 'checkout'

urlpatterns = [
    path('', views.checkout_page, name='checkout_page'),
    path('success/<str:order_id>/', views.order_success, name='order_success'),
    path('track/', views.track_order, name='track_order'),
    path('track/<str:order_id>/', views.track_order, name='track_order_detail'),
    path('payment-status/<str:order_id>/', views.payment_status, name='payment_status'),
    path('receipt/<str:order_id>/', views.download_receipt, name='download_receipt'),
    
    # ===== COUPON URLs =====
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('remove-coupon/', views.remove_coupon, name='remove_coupon'),
]