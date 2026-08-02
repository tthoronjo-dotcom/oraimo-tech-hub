from django import forms
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox


class ContactForm(forms.Form):
    """
    Contact form with reCAPTCHA for spam protection
    """
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name',
            'required': True
        }),
        label='Full Name'
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your@email.com',
            'required': True
        }),
        label='Email Address'
    )
    
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'What is this regarding?',
            'required': True
        }),
        label='Subject'
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Your message here...',
            'required': True
        }),
        label='Message'
    )
    
    # ===== RECAPTCHA =====
    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(
            attrs={
                'data-theme': 'dark',  # Matches your dark theme
                'data-size': 'normal',
            }
        ),
        label=''
    )
    
    def clean_email(self):
        """Validate email format"""
        email = self.cleaned_data.get('email')
        if email:
            try:
                validate_email(email)
            except ValidationError:
                raise forms.ValidationError("Please enter a valid email address.")
        return email
    
    def clean_name(self):
        """Validate name has at least 2 characters"""
        name = self.cleaned_data.get('name')
        if name and len(name.strip()) < 2:
            raise forms.ValidationError("Name must be at least 2 characters.")
        return name.strip()
    
    def clean_message(self):
        """Validate message has at least 10 characters"""
        message = self.cleaned_data.get('message')
        if message and len(message.strip()) < 10:
            raise forms.ValidationError("Message must be at least 10 characters.")
        return message.strip()