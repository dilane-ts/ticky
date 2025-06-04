from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

class LoginForm(forms.Form):
    phone = forms.CharField(required=True)
    password = forms.CharField(required=True)


class RegisterForm(forms.Form):
    name = forms.CharField(required=True)
    phone = forms.CharField(
        required=True,
        validators=[
            RegexValidator(
                regex=r'^\+2376[7,8,5,9][0-9]{7}$',
                message="Le numero n'est pas valide (+2376xxxxxxxx)"
            )
        ]
    )
    email = forms.EmailField(required=False)
    password = forms.CharField(required=True)
    
    def clean_phone(self):
        phone = self.cleaned_data['phone']
        # Check if phone already exists
        from .models import User
        if User.objects.filter(phone=phone).exists():
            raise ValidationError("Ce numéro de téléphone est déjà utilisé")
        return phone
