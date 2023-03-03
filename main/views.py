import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView, PasswordChangeView, PasswordResetView, PasswordResetDoneView
from django.contrib.auth.views import PasswordResetConfirmView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import CreateView, UpdateView
from django.views.generic.edit import DeleteView
from django.views.generic.base import ContextMixin
from django.core.signing import BadSignature
from django.urls import reverse_lazy

from .forms import UserLoginForm, UserRegistrationForm, ChangeUserInfoForm
from .utilities import signer, get_activation_host
from .models import BookUser

logger = logging.getLogger(__name__)

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

class RegisterUser(CreateView):

    form_class = UserRegistrationForm
    template_name = 'main/register.html'
    success_url = reverse_lazy('main:register_done')

def register_done(request):
    return render(request, 'main/register_done.html')

def user_activate(request, sign):

    try:
        username = signer.unsign(sign)
    except BadSignature:
        return render(request, 'main/wrong_activation.html')

    user = get_object_or_404(BookUser, username=username)

    if not user.is_active:
        user.is_active = True
        user.is_activated = True
        user.save()
        
    return render(request, 'main/user_active.html')

def ping(request):
    logger.warning(get_activation_host())
    return render(request, 'main/ping.html')

@login_required
def profile(request):

    context = {
        'user': request.user,
        'fullname': request.user.get_full_name(),
    }

    return render(request, 'main/profile.html', context)

class ChangeUserInfoView(SuccessMessageMixin, LoginRequiredMixin, UpdateView, ContextMixin):

    model = BookUser
    template_name = 'main/change_user_info.html'
    form_class = ChangeUserInfoForm
    success_url = reverse_lazy('main:profile')
    success_message = 'Данные пользователя изменены'

    def setup(self, request, *args, **kwargs):
        self.current_user = request.user
        self.user_id = request.user.pk
        return super().setup(request, *args, **kwargs)
    
    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=self.user_id)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fullname'] = self.current_user.get_full_name()
        return context

class PasswordChangeView(SuccessMessageMixin, LoginRequiredMixin, PasswordChangeView):

    template_name = 'main/password_change.html'
    success_url = reverse_lazy('main:profile')
    success_message = 'Пароль изменен'

class DeleteUserView(LoginRequiredMixin, DeleteView):

    model = BookUser
    template_name = 'main/delete_user.html'
    success_url = reverse_lazy('main:index')

    def setup(self, request, *args, **kwargs):
        self.user_id = request.user.pk
        return super().setup(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        logout(request)
        messages.add_message(request, messages.SUCCESS, 'Пользователь удален')
        return super().post(request, *args, **kwargs)
    
    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=self.user_id)
    
class UserPasswordResetView(PasswordResetView):

    template_name = 'main/password_reset.html'
    subject_template_name = 'email/password_reset_subject.txt'
    email_template_name = 'email/password_reset_body.txt'
    success_url = reverse_lazy('main:password_reset_done')

class UserPasswordResetDoneView(PasswordResetDoneView):

    template_name = 'main/password_reset_done.html'

class UserPasswordResetConfirmView(PasswordResetConfirmView):

    template_name = 'main/password_reset.html'
    post_reset_login = True
    success_url = reverse_lazy('main:profile')
