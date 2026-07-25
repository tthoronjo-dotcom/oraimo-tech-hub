from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView
from shop.views import home_page
from payment.views import pesapal_callback, pesapal_ipn
from shop.views import dashboard_view
from shop.views import privacy_policy, terms_of_service, returns_policy, faq_page

urlpatterns = [
    # ===== DASHBOARD — MUST COME BEFORE ADMIN =====
    path('adteddymin/reports/', dashboard_view, name='reports_dashboard'),
    
    # ===== ADMIN =====
    path('adteddymin/', admin.site.urls),
    
    # ===== MAIN PAGES =====
    path('', home_page, name='home'),
    path('shop/', include('shop.urls')),
    path('basket/', include('basket.urls')),
    path('checkout/', include('checkout.urls')),
    path('contact/', include('contact.urls')),
    path('accounts/', include('accounts.urls')),
    
    # ===== FOOTER PAGES =====
    path('privacy/', privacy_policy, name='privacy_policy'),
    path('terms/', terms_of_service, name='terms_of_service'),
    path('returns/', returns_policy, name='returns_policy'),
    path('faq/', faq_page, name='faq_page'),
    
    # ===== PAYMENT & OTHER =====
    path('api/pesapal/callback/', pesapal_callback, name='pesapal_callback'),
    path('api/pesapal/ipn/', pesapal_ipn, name='pesapal_ipn'),
    path('captcha/', include('captcha.urls')),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    handler404 = 'core.views.custom_404'
    handler403 = 'core.views.custom_403'
    handler500 = 'core.views.custom_500'