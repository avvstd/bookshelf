import datetime
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .apps import user_registered
from .models import BookUser, Shelf, ShelfRecord

class DateInput(forms.DateInput):
    input_type = 'date'

class UserLoginForm(AuthenticationForm):

    username = forms.CharField(
        label= 'Логин', 
        widget= forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Логин', 'autofocus': ''}),
        required= True
    )

    password = forms.CharField(
        label= 'Пароль', 
        widget= forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Пароль'}),
        required= True
    )

    remember_me = forms.BooleanField(required = False)

class UserRegistrationForm(UserCreationForm):

    username = forms.CharField(
        label= 'Логин', 
        widget= forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Логин', 'autofocus': ''}),
        required= True
    )

    email = forms.EmailField(
        label='Эл. почта',
        widget= forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Эл. почта'}),
        required= True
    )

    password1 = forms.CharField(
        label= 'Введите пароль', 
        widget= forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Введите пароль'}),
        required= True
    )

    password2 = forms.CharField(
        label= 'Повторите пароль', 
        widget= forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Повторите пароль'}),
        required= True
    )

    class Meta:

        model = BookUser
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit)
        user.is_active = False
        user.is_activated = False
        if commit:
            user.save()
        user_registered.send(UserRegistrationForm, instance=user)
        return user
    
class ChangeUserInfoForm(forms.ModelForm):

    email = forms.EmailField(
        label ='Электронная почта',
        widget = forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Электронная почта'}),
        required = True
    )

    class Meta:
        model = BookUser
        fields = ('username', 'email', 'first_name', 'last_name', 'sex', 'userpic')

class ShelfForm(forms.ModelForm):

    class Meta:
        model = Shelf
        fields = '__all__'
        widgets = {
            'owner': forms.HiddenInput,
            'private': forms.widgets.Select(attrs={'size': 1})  #bootstrap compatibility
        }

class RecorddAddForm(forms.ModelForm):

    class Meta:
        model = ShelfRecord
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название'}),
            'author': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Автор'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Комментарий', 'rows': 5}),
            'rating': forms.widgets.Select(attrs={'size': 1, 'class': 'form-control'}),
            'read_date': DateInput(attrs={'class': 'form-control', 'placeholder': 'Дата'}),
            'cover': forms.FileInput(attrs={'class': 'form-control'}),
            'shelf': forms.HiddenInput,
        }