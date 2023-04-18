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
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from random import randint

from .forms import UserLoginForm, UserRegistrationForm, ChangeUserInfoForm, ShelfForm, RecorddAddForm
from .forms import UploadFileForm
from .utilities import signer, handle_shelf_file
from .models import BookUser, Shelf, ShelfRecord
from bookshelf.settings import DEBUG

if DEBUG:
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

    context = {'form': form, 'title': 'Добавление полки'}

    return render(request, 'main/shelf_change.html', context)

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
        paginator = Paginator(records, 15)
        if 'page' in request.GET:
            page_num = request.GET['page']
        else:
            page_num = 1

        page = paginator.get_page(page_num)
        valid_numbers = get_valid_numbers_of_page(paginator.num_pages, 2, int(page_num))
        context = {
            'name': shelf.name,
            'shelfrecords': page.object_list,
            'is_owner': is_owner,
            'pk': pk,
            'page': page,
            'valid_numbers': valid_numbers,
            'num_pages': paginator.num_pages
        }
        return render(request, 'main/shelf_detail.html', context)
    
@login_required
def record_add(request, pk):
    shelf = get_object_or_404(Shelf, pk=pk)
    user = request.user
    is_owner = (shelf.owner == user)

    if not is_owner:
        raise PermissionDenied()
    
    book_cover_random_postfix = randint(1, 6)

    if request.method == 'POST':
        form = RecorddAddForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, 'Запись добавлена')
            return redirect('main:shelf_detail', pk=pk)                
    else:
        form = RecorddAddForm(initial={
                                'shelf': pk, 
                                'read_date': datetime.date.today().isoformat(),
                                'random_cover': book_cover_random_postfix
                            })
        
    context = {
        'form': form, 
        'name': shelf.name, 
        'pk': pk, 
        'cover': 'main/book_%d.svg' % book_cover_random_postfix,
        'title': 'Добавление записи'
        }
    return render(request, 'main/record_change.html', context)

@login_required
def shelf_change(request, pk):
    shelf = get_object_or_404(Shelf, pk=pk)

    if shelf.owner != request.user:
        raise PermissionDenied()

    if request.method == 'POST':
        form = ShelfForm(request.POST, instance=shelf)
        if form.is_valid():
            form.save()
            return redirect('main:shelf_detail', pk=pk)
    else:
        form = ShelfForm(instance=shelf)

    context = {'form': form, 'title': 'Редактирование полки'}

    return render(request, 'main/shelf_change.html', context)

@login_required
def shelf_delete(request, pk):
    shelf = get_object_or_404(Shelf, pk=pk)
    if shelf.owner != request.user:
        raise PermissionDenied()
    
    if request.method == 'POST':
        shelf.delete()
        messages.add_message(request, messages.SUCCESS, 'Полка удалена')
        return redirect('main:profile')
    else:
        context = {'name': shelf.name}
        return render(request, 'main/delete_shelf.html', context)

@login_required
def record_detail(request, pk):
    record = get_object_or_404(ShelfRecord, pk=pk)
    if record.shelf.owner != request.user:
        raise PermissionDenied()

    context = {
        'cover': record.cover,
        'title': record.title,
        'random_cover': record.random_cover,
        'pk_shelf': record.shelf.pk,
        'name': record.shelf.name,
        'author': record.author,
        'rating': record.rating,
        'read_date': record.read_date,
        'comment': record.comment,
        'pk': record.pk,
        }
    return render(request, 'main/record_detail.html', context)

@login_required
def record_change(request, pk):
    record = get_object_or_404(ShelfRecord, pk=pk)

    if record.shelf.owner != request.user:
        raise PermissionDenied()

    if request.method == 'POST':
        form = RecorddAddForm(request.POST, request.FILES, instance=record)
        logger.warning(type(request.FILES))
        logger.warning(request.FILES)
        if form.is_valid():
            form.save()
            return redirect('main:shelf_detail', pk=record.shelf.pk)
    else:
        form = RecorddAddForm(instance=record)

    context = {
        'form': form, 
        'name': record.shelf.name, 
        'pk': record.shelf.pk, 
        'cover': record.cover,
        'random_cover': record.random_cover,
        'rating': record.rating,
        'title': 'Редактирование записи'
        }

    return render(request, 'main/record_change.html', context)

@login_required
def record_delete(request, pk):
    record = get_object_or_404(ShelfRecord, pk=pk)
    if record.shelf.owner != request.user:
        raise PermissionDenied()
    
    if request.method == 'POST':
        record.delete()
        messages.add_message(request, messages.SUCCESS, 'Запись удалена')
        return redirect('main:shelf_detail', pk=record.shelf.pk)
    else:
        context = {'title': record.title}
        return render(request, 'main/delete_record.html', context)

def page_not_found_view(request, exception):
    context = {'status': '404', 'status_message': 'Страница не найдена'}
    return render(request, 'main/bad_code.html', context)

def forbidden_view(request, exception):
    context = {'status': '403', 'status_message': 'Доступ запрещен'}
    return render(request, 'main/bad_code.html', context)

def server_error_view(request):
    context = {'status': '500', 'status_message': 'Внутренняя ошибка'}
    return render(request, 'main/bad_code.html', context)

@login_required
def shelf_upload(request, pk):
    shelf = get_object_or_404(Shelf, pk=pk)
    if shelf.owner != request.user:
        raise PermissionDenied()
    
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            data = handle_shelf_file(request.FILES['file'])
            create_records(data, shelf)
            return redirect('main:shelf_detail', pk=pk)
    else:
        form = UploadFileForm()

    return render(request, 'main/shelf_upload.html', {'form': form})

def create_records(data, shelf):

    for element in data:

        record = ShelfRecord()
        record.title = element['title']
        record.author = element['author']
        record.rating = element['rating']
        record.read_date = element['read_date']
        record.shelf = shelf
        record.random_cover = randint(1, 6)
        record.save()

    return 0
    
def get_valid_numbers_of_page(num_pages, half_portion, number):
    result = []
    if num_pages <= 0 or number > num_pages or half_portion <= 0:
        return result
    else:
        max_elements = min(num_pages, 2 * half_portion + 1)
        result.append(number)
        stop_it = False
        for i in range(1, 2 * half_portion + 1):
            for j in [-1, 1]:
                current = number + j * i
                if current > 0 and current <= num_pages:
                    result.append(current)
                if len(result) >= max_elements:
                    stop_it = True
                    break
            if stop_it:
                break

    result.sort()
    return result
