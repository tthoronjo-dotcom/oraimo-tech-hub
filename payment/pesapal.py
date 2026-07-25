import requests
import logging
from decouple import config

logger = logging.getLogger(__name__)

class PesapalClient:
    def __init__(self):
        self.consumer_key = config('PESAPAL_CONSUMER_KEY', default='')
        self.consumer_secret = config('PESAPAL_CONSUMER_SECRET', default='')
        self.environment = config('PESAPAL_ENVIRONMENT', default='sandbox')
        self.callback_url = config('PESAPAL_CALLBACK_URL', default='')
        self.ipn_url = config('PESAPAL_IPN_URL', default='')
        self.timeout = config('PESAPAL_TIMEOUT', default=30, cast=int)
        
        if self.environment == 'sandbox':
            self.base_url = 'https://cybqa.pesapal.com/pesapalv3/api'
        else:
            self.base_url = 'https://pay.pesapal.com/v3/api'
    
    def get_access_token(self):
        if not self.consumer_key or not self.consumer_secret:
            logger.error("PESAPAL_CONSUMER_KEY or PESAPAL_CONSUMER_SECRET not set")
            return None
            
        try:
            url = f"{self.base_url}/Auth/RequestToken"
            payload = {
                'consumer_key': self.consumer_key,
                'consumer_secret': self.consumer_secret
            }
            response = requests.post(url, json=payload, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('token')
            else:
                logger.error(f"Failed to get Pesapal token: {response.status_code} - {response.text}")
                return None
                
        except requests.Timeout:
            logger.error("Timeout getting Pesapal access token")
            return None
        except Exception as e:
            logger.error(f"Error getting Pesapal access token: {str(e)}")
            return None
    
    def submit_order(self, order, amount, phone=None, email=None, description=None):
        try:
            token = self.get_access_token()
            if not token:
                return {'error': 'Failed to get Pesapal access token'}
            
            url = f"{self.base_url}/Transactions/SubmitOrderRequest"
            merchant_reference = order.order_id
            desc = description or f'Oraimo Order {order.order_id}'
            
            order_data = {
                'id': merchant_reference,
                'currency': 'KES',
                'amount': float(amount),
                'description': desc,
                'callback_url': self.callback_url,
                'ipn_url': self.ipn_url,
                'notification_type': 'SMS',
                'billing_address': {
                    'email_address': email or order.customer_email,
                    'phone_number': phone or order.customer_phone,
                    'country_code': 'KE',
                    'first_name': order.customer_name,
                    'last_name': order.customer_name
                }
            }
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, json=order_data, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'redirect_url': data.get('redirect_url'),
                    'order_tracking_id': data.get('order_tracking_id'),
                    'merchant_reference': data.get('merchant_reference')
                }
            else:
                logger.error(f"Pesapal submit order failed: {response.status_code} - {response.text}")
                return {'error': f'Failed to submit order: {response.status_code}'}
                
        except requests.Timeout:
            logger.error("Timeout submitting order to Pesapal")
            return {'error': 'Request timeout'}
        except Exception as e:
            logger.error(f"Error submitting order to Pesapal: {str(e)}")
            return {'error': str(e)}
    
    def query_payment_status(self, order_tracking_id):
        try:
            token = self.get_access_token()
            if not token:
                return {'error': 'Failed to get Pesapal access token'}
            
            url = f"{self.base_url}/Transactions/GetTransactionStatus"
            params = {'orderTrackingId': order_tracking_id}
            headers = {'Authorization': f'Bearer {token}'}
            
            response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Pesapal query status failed: {response.status_code} - {response.text}")
                return {'error': f'Failed to query status: {response.status_code}'}
                
        except requests.Timeout:
            logger.error("Timeout querying Pesapal status")
            return {'error': 'Request timeout'}
        except Exception as e:
            logger.error(f"Error querying Pesapal status: {str(e)}")
            return {'error': str(e)}