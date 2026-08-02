from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .forms import ContactForm


def contact_page(request):
    """
    Contact page view with reCAPTCHA
    """
    if request.method == 'POST':
        form = ContactForm(request.POST)
        
        if form.is_valid():
            # Get cleaned data
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            
            # Build email
            email_subject = f"Contact Form: {subject}"
            email_body = f"""
You have received a new message from your website contact form.

Name: {name}
Email: {email}
Subject: {subject}

Message:
{message}
            """
            
            try:
                # Send email using SendGrid (or SMTP)
                send_mail(
                    subject=email_subject,
                    message=email_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.ADMIN_EMAIL],
                    fail_silently=False,
                )
                
                messages.success(
                    request, 
                    '✅ Your message has been sent successfully! We will get back to you soon.'
                )
                return redirect('contact:contact')
                
            except Exception as e:
                messages.error(
                    request, 
                    '❌ Failed to send your message. Please try again or contact us via WhatsApp.'
                )
                print(f"Email error: {e}")
        else:
            # Form has errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    else:
        form = ContactForm()
    
    return render(request, 'contact/contact.html', {'form': form})