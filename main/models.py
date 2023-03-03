from django.db import models
from django.contrib.auth.models import AbstractUser
from .utilities import get_upload_path

class BookUser(AbstractUser):
    is_activated = models.BooleanField(default=False, verbose_name='Активирован', db_index=True)
    userpic = models.ImageField(upload_to=get_upload_path, null=True, blank=True, verbose_name='Аватар')
    sex = models.BooleanField(default=True, verbose_name='Пол', choices=[(True, 'Мужской'), (False, 'Женский')])
    email = models.EmailField(verbose_name='Электронная почта', 
                              max_length=254, null=False, blank=False, 
                              unique=True, db_index=True, 
                              error_messages={'unique': 'Пользователь с такой электронной почтой уже существует.'})
