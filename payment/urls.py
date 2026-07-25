from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    # Pesapal is DISABLED for COD mode
    # These URLs will redirect to home or show a message
    path('pesapal/callback/', views.pesapal_callback, name='pesapal_callback'),
    path('pesapal/ipn/', views.pesapal_ipn, name='pesapal_ipn'),
]