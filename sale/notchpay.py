import requests
from django.urls import reverse
import uuid

def get_operator(phone):
    # Remove any non-digit characters and ensure it's a string
    phone = str(phone).strip().replace(" ", "")

    # Check for '+237' prefix and then extract the 9-digit number
    if phone.startswith('+237'):
        phone = phone[4:] # Remove '+237'
    else:
        return "Invalid Cameroon Phone Number Format (missing +237 prefix)"

    # All mobile numbers in Cameroon are 9 digits long and start with '6'
    if not (phone.startswith('6') and len(phone) == 9 and phone.isdigit()):
        return "Invalid Cameroon Mobile Number Format (after +237)"

    # Get the second digit (after the initial '6')
    second_digit = int(phone[1])
    # Get the first three digits of the local number (after the initial '6')
    first_three_digits = int(phone[1:4])

    # MTN Cameroon Prefixes
    # The second digit is 7 or 8, OR the first three digits are between 650 and 654
    if second_digit in [7, 8]:
        return "MTN"
    elif 50 <= first_three_digits <= 54:
        return "MTN"

    # Orange Cameroon Prefixes
    # The second digit is 9, OR the first three digits are between 655 and 659
    elif second_digit == 9:
        return "Orange"
    elif 55 <= first_three_digits <= 59:
        return "Orange"
    
    # If it starts with '6' but doesn't match MTN or Orange, it might be Nexttel or other
    # However, the request specifically asked for only Orange and MTN.
    return "Unknown Operator (neither MTN nor Orange)"


class NotchPay:
    def __init__(self, public_api_key, order):
        self.base_url = "https://api.notchpay.co"
        self.public_api_key = public_api_key
        self.headers = {
            "Authorization": self.public_api_key,
            "Content-Type": "application/json"
        }
        self.order = order

    def initialize(self, request, amount):
        reference = "ti_" + str(self.order.pk) + "_" + str(uuid.uuid4())
        callback_url = request.build_absolute_uri(reverse('payment_sucess'))
        print(callback_url)
        payload = {
            "amount": int(amount),
            "currency": "XAF",
            "customer": {
                "name": self.order.user.username,
                "email": self.order.user.email,
                "phone": self.order.user.phone
            },
            "description": f"Payment for self.order {self.order.pk}",
            "reference": reference,
            "callback": callback_url,
        }
        
        response = requests.post(f"{self.base_url}/payments/initialize", headers=self.headers, json=payload)
        if response.status_code == 201:
            data = response.json()
            print(data)
            self.order.reference = data['transaction']['reference']
            self.order.save()
            return data
        else:
            raise ValueError(response.json()['message'])
        
    def complete(self):
        operator = get_operator(self.order.user.phone)
        if operator not in ["MTN", "Orange"]:
            raise ValueError(operator)
        
        payload = {
            "channel": "cm.mtn" if operator == "MTN" else "cm.orange",
            "data": {
                "phone": self.order.user.phone
            }
        }
        response = requests.post(f"{self.base_url}/payments/{self.order.reference}", headers=self.headers, json=payload)
        print(response.json())
        if response.status_code == 202:
            data = response.json()
            return data
        else:
            print(response.json())
            raise ValueError(response.json()['message'])

