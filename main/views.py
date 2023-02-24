from django.shortcuts import render, redirect
from datetime import datetime
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required

from .forms import UserLoginForm

def index(request):
    ''' Main page. '''
    return render(request, 'main/index.html')

class UserLoginView(LoginView):

    form_class = UserLoginForm
    template_name = 'main/login.html'
    next_page = 'main:index'

    def form_valid(self, form):

        remember_me = form.cleaned_data.get('remember_me')

        if not remember_me:
            self.request.session.set_expiry(0)
            self.request.session.modified = True

        return super(UserLoginView, self).form_valid(form)

@login_required
def user_logout(request):
    logout(request)
    return redirect('main:login')