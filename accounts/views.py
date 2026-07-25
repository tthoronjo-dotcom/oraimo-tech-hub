from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from checkout.models import Order
from core.emails import send_welcome_email
from basket.basket import Basket

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome {user.username}!')
            
            # Merge guest basket with user's saved basket
            basket = Basket(request)
            basket.merge_with_user_basket(user)
            
            # Send welcome email
            send_welcome_email(user)
            
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Merge guest basket with user's saved basket
        basket = Basket(self.request)
        basket.merge_with_user_basket(self.request.user)
        return response

class CustomLogoutView(LogoutView):
    next_page = '/'
    
    def dispatch(self, request, *args, **kwargs):
        # Save basket to user before logout
        if request.user.is_authenticated:
            basket = Basket(request)
            basket.save_to_user(request.user)
        return super().dispatch(request, *args, **kwargs)

@login_required
def profile_view(request):
    orders = Order.objects.filter(customer_email=request.user.email).order_by('-created_at')
    return render(request, 'accounts/profile.html', {
        'orders': orders,
        'user': request.user,
    })