from django.shortcuts import redirect
from django.urls import reverse

class AdminAccessMiddleware:
    """
    Block non-staff users from accessing the admin panel.
    Authenticated non-staff users get redirected to home.
    Unauthenticated users are handled by Django's login.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Block non-staff users from accessing admin
        if request.path.startswith('/admin/') and request.user.is_authenticated:
            if not request.user.is_staff:
                return redirect('/')
        return self.get_response(request)