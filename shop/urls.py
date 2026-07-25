from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('api/search/', views.search_api, name='search_api'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('product/<slug:slug>/review/', views.add_review, name='add_review'),
    path('<slug:slug>/', views.product_detail, name='product_detail'),
]