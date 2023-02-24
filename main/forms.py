from django import forms
from django.contrib.auth.forms import AuthenticationForm

class UserLoginForm(AuthenticationForm):

    username = forms.CharField(
        label= 'Логин', 
        widget= forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Логин', 'autofocus': ''}),
        required= True
    )

    password = forms.CharField(
        label= 'Пароль', 
        widget= forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Пароль'})
    )

    remember_me = forms.BooleanField(required = False)