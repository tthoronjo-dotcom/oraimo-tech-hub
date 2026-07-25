from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='reports_dashboard'),
    path('api/sales/', views.api_sales_summary, name='reports_sales'),
    path('api/top-products/', views.api_top_products, name='reports_top_products'),
    path('api/payment-stats/', views.api_payment_stats, name='reports_payment_stats'),
    path('api/category-sales/', views.api_category_sales, name='reports_category_sales'),
    path('api/delivery-stats/', views.api_delivery_stats, name='reports_delivery_stats'),
    path('api/recent-orders/', views.api_recent_orders, name='reports_recent_orders'),
]