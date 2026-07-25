from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .forms import ContactForm

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            full_message = f'From: {name} <{email}>\n\n{message}'
            
            try:
                send_mail(
                    subject=f'Contact: {subject}',
                    message=full_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.ADMIN_EMAIL],
                    fail_silently=False,
                )
                messages.success(request, '✅ Your message has been sent! We\'ll get back to you soon.')
                return redirect('contact')
            except Exception as e:
                messages.error(request, '❌ There was an error sending your message. Please try again.')
                print(f"Contact form error: {e}")
        else:
            messages.error(request, '❌ Please correct the errors below.')
    else:
        form = ContactForm()
    
    return render(request, 'contact/contact.html', {'form': form})