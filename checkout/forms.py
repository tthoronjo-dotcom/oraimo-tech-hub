from django import forms
from .models import Order

class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'customer_name', 'customer_phone', 'customer_email',
            'delivery_location', 'delivery_address', 'is_cbd',
            'delivery_notes', 'marketing_consent'
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name'
            }),
            'customer_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 0712345678 or 254712345678'
            }),
            'customer_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your@email.com'
            }),
            'delivery_location': forms.Select(attrs={
                'class': 'form-select',
                'id': 'delivery-location'
            }),
            'delivery_address': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Street name, building, apartment number'
            }),
            'delivery_notes': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control',
                'placeholder': 'Any special instructions for delivery? (Optional)'
            }),
            'is_cbd': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'marketing_consent': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'customer_name': 'Full Name',
            'customer_phone': 'Phone Number',
            'customer_email': 'Email Address',
            'delivery_location': 'Delivery Location/Area',
            'delivery_address': 'Detailed Delivery Address',
            'is_cbd': 'CBD Delivery (Free Delivery)',
            'delivery_notes': 'Delivery Notes (Optional)',
            'marketing_consent': 'I agree to receive marketing communications',
        }
        help_texts = {
            'customer_phone': 'Enter a valid Kenyan phone number',
            'delivery_location': 'Select your delivery area',
            'delivery_address': 'Complete address for delivery',
            'delivery_notes': 'E.g., "Call before delivery" or "Gate code: 1234"',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make delivery_location required
        self.fields['delivery_location'].required = True
        # Set empty label - this creates a blank first option
        self.fields['delivery_location'].empty_label = '— Select your delivery location —'
        # Make all fields required except optional ones
        self.fields['customer_email'].required = False
        self.fields['delivery_notes'].required = False
        self.fields['marketing_consent'].required = False
    
    def clean_phone(self):
        """Validate and format Kenyan phone number"""
        phone = self.cleaned_data.get('customer_phone')
        if not phone:
            return phone
        
        # Remove any spaces, dashes, or special characters
        phone = ''.join(filter(str.isdigit, phone))
        
        # Validate Kenyan phone number formats
        if phone.startswith('0') and len(phone) == 10:
            phone = '254' + phone[1:]
        elif phone.startswith('254') and len(phone) == 12:
            pass
        elif phone.startswith('+254') and len(phone) == 13:
            phone = phone[1:]
        else:
            raise forms.ValidationError(
                "Please enter a valid Kenyan phone number (e.g., 0712345678, 254712345678, or +254712345678)"
            )
        
        return phone
    
    def clean(self):
        """Additional validation"""
        cleaned_data = super().clean()
        delivery_location = cleaned_data.get('delivery_location')
        
        if not delivery_location or delivery_location == '':
            raise forms.ValidationError({
                'delivery_location': 'Please select a delivery location.'
            })
        
        return cleaned_data