import logging, datetime

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
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy

from .forms import UserLoginForm, UserRegistrationForm, ChangeUserInfoForm, ShelfForm, RecorddAddForm
from .utilities import signer, get_activation_host
from .models import BookUser, Shelf, ShelfRecord

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
    context = {
            'title': 'Активация',
            'message': 'Для окончания регистрации пользователя перейдите по ссылке,'
                + ' в письме, высланном на Вашу электронную почту.'
        }
    return render(request, 'layout/simple.html', context)

def user_activate(request, sign):

    template_name = 'layout/simple.html'

    try:
        username = signer.unsign(sign)
    except BadSignature:
        context = {
            'title': 'Ошибка активации',
            'message': 'Активация пользователя прошла неудачно.'
        }
        return render(request, template_name, context)

    user = get_object_or_404(BookUser, username=username)

    if not user.is_active:
        user.is_active = True
        user.is_activated = True
        user.save()
        
    context = {
        'title': 'Активация',
        'message': 'Пользователь активирован.'
    }

    return render(request, template_name, context)

def ping(request):
    logger.warning(get_activation_host())
    context = {
            'title': 'Pong',
            'message': 'Pong.'
        }
    return render(request, 'layout/simple.html', context)

@login_required
def profile(request):

    shelfs = Shelf.objects.filter(owner=request.user.pk)

    context = {
        'user': request.user,
        'fullname': request.user.get_full_name(),
        'shelfs': shelfs
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
    extra_context = {'label': 'Укажите адрес электронной почты для сброса пароля.', }

class UserPasswordResetDoneView(PasswordResetDoneView):

    template_name = 'layout/simple.html'
    extra_context = {
        'title': 'Изменение пароля',
        'message': 'На электронную почту отправлена ссылка для изменения пароля.'
    }

class UserPasswordResetConfirmView(PasswordResetConfirmView):

    template_name = 'main/password_reset.html'
    post_reset_login = True
    success_url = reverse_lazy('main:profile')

@login_required
def shelf_add(request):

    if request.method == 'POST':
        form = ShelfForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('main:profile')
    else:
        form = ShelfForm(initial={'owner': request.user.pk})

    context = {'form': form}

    return render(request, 'main/shelf_add.html', context)

def shelf_detail(request, pk):

    shelf = get_object_or_404(Shelf, pk=pk)
    user = request.user
    is_owner = (shelf.owner == user)
    access_denied = (shelf.private and not is_owner)
    
    if access_denied:
        context = {
            'title': 'Книжная полка',
            'message': 'У Вас нет доступа к этой полке.'
        }
        return render(request, 'layout/simple.html', context)
    else:
        records = ShelfRecord.objects.filter(shelf=shelf.pk)
        context = {
            'name': shelf.name,
            'shelfrecords': records,
            'is_owner': is_owner,
            'pk': pk
        }
        return render(request, 'main/shelf_detail.html', context)
    
@login_required
def record_add(request, pk):
    shelf = get_object_or_404(Shelf, pk=pk)
    user = request.user
    is_owner = (shelf.owner == user)

    if not is_owner:
        raise PermissionDenied()
    
    if request.method == 'POST':
        form = RecorddAddForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, 'Запись добавлена')
            return redirect('main:shelf_detail', pk=pk)                
    else:
        form = RecorddAddForm(initial={
                                'shelf': pk, 
                                'read_date': datetime.date.today().isoformat()
                            })
        
    context = {'form': form, 'name': shelf.name, 'pk': pk}
    return render(request, 'main/shelf_record_add.html', context)