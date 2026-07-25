import requests
import base64
import logging
from datetime import datetime
from decouple import config
from .models import MpesaTransaction

logger = logging.getLogger(__name__)


class MpesaClient:
    def __init__(self):
        self.consumer_key = config('MPESA_CONSUMER_KEY', default='')
        self.consumer_secret = config('MPESA_CONSUMER_SECRET', default='')
        self.passkey = config('MPESA_PASSKEY', default='')
        self.shortcode = config('MPESA_SHORTCODE', default='174379')
        self.callback_url = config('MPESA_CALLBACK_URL', default='')
        self.environment = config('MPESA_ENVIRONMENT', default='sandbox')
        self.timeout = config('MPESA_TIMEOUT', default=30, cast=int)
    
    def _get_url(self, path):
        base = 'https://sandbox.safaricom.co.ke' if self.environment == 'sandbox' else 'https://api.safaricom.co.ke'
        return f"{base}{path}"
    
    def get_access_token(self):
        """Get OAuth access token from Safaricom"""
        if not self.consumer_key or not self.consumer_secret:
            logger.error("MPESA_CONSUMER_KEY or MPESA_CONSUMER_SECRET not set")
            return None
            
        try:
            url = self._get_url('/oauth/v1/generate?grant_type=client_credentials')
            auth = base64.b64encode(f"{self.consumer_key}:{self.consumer_secret}".encode()).decode()
            headers = {'Authorization': f'Basic {auth}'}
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json().get('access_token')
            else:
                logger.error(f"Failed to get access token: {response.status_code} - {response.text}")
                return None
                
        except requests.Timeout:
            logger.error("Timeout getting access token")
            return None
        except Exception as e:
            logger.error(f"Error getting access token: {str(e)}")
            return None
    
    def stk_push(self, phone_number, amount, order_id, checkout_id):
        """Initiate STK Push transaction"""
        try:
            access_token = self.get_access_token()
            if not access_token:
                return {'error': 'Failed to get access token'}
            
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password = base64.b64encode(f"{self.shortcode}{self.passkey}{timestamp}".encode()).decode()
            
            # Format phone number
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            elif phone_number.startswith('+'):
                phone_number = phone_number[1:]
            
            payload = {
                'BusinessShortCode': self.shortcode,
                'Password': password,
                'Timestamp': timestamp,
                'TransactionType': 'CustomerPayBillOnline',
                'Amount': int(amount),
                'PartyA': phone_number,
                'PartyB': self.shortcode,
                'PhoneNumber': phone_number,
                'CallBackURL': self.callback_url,
                'AccountReference': order_id,
                'TransactionDesc': f'Oraimo Order {order_id}'
            }
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            url = self._get_url('/mpesa/stkpush/v1/processrequest')
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            result = response.json()
            
            # Store the transaction
            if 'CheckoutRequestID' in result:
                MpesaTransaction.objects.create(
                    checkout_request_id=result['CheckoutRequestID'],
                    order_id=order_id,
                    phone_number=phone_number,
                    amount=amount,
                    status='pending'
                )
                logger.info(f"STK Push initiated for order {order_id}: {result['CheckoutRequestID']}")
            
            return result
            
        except requests.Timeout:
            logger.error(f"Timeout during STK Push for order {order_id}")
            return {'error': 'Request timeout'}
        except Exception as e:
            logger.error(f"STK Push error: {str(e)}")
            return {'error': str(e)}
    
    def query_status(self, checkout_request_id):
        """Query the status of a transaction"""
        try:
            access_token = self.get_access_token()
            if not access_token:
                return {'error': 'Failed to get access token'}
            
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password = base64.b64encode(f"{self.shortcode}{self.passkey}{timestamp}".encode()).decode()
            
            payload = {
                'BusinessShortCode': self.shortcode,
                'Password': password,
                'Timestamp': timestamp,
                'CheckoutRequestID': checkout_request_id
            }
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            url = self._get_url('/mpesa/stkpushquery/v1/query')
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            
            return response.json()
            
        except requests.Timeout:
            logger.error(f"Timeout querying status for {checkout_request_id}")
            return {'error': 'Request timeout'}
        except Exception as e:
            logger.error(f"Query status error: {str(e)}")
            return {'error': str(e)}