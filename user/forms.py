from django import forms

class LoginForm(forms.Form):
    phone = forms.CharField(required=True)
    password = forms.CharField(required=True)


class RegisterForm(forms.Form):
    name = forms.CharField(required=True)
    phone = forms.CharField(required=True)
    email = forms.CharField(required=False)
    password = forms.CharField(required=True)