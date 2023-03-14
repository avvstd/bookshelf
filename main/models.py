from django.db import models
from django.contrib.auth.models import AbstractUser
from .utilities import get_userpics_upload_path, get_covers_upload_path

class BookUser(AbstractUser):
    is_activated = models.BooleanField(default=False, verbose_name='Активирован', db_index=True)
    userpic = models.ImageField(upload_to=get_userpics_upload_path, null=True, blank=True, verbose_name='Аватар')
    sex = models.BooleanField(default=True, verbose_name='Пол', choices=[(True, 'Мужской'), (False, 'Женский')])
    email = models.EmailField(verbose_name='Электронная почта', 
                              max_length=254, null=False, blank=False, 
                              unique=True, db_index=True, 
                              error_messages={'unique': 'Пользователь с такой электронной почтой уже существует.'})
    
    def delete(self, *args, **kwargs):
        for shelf in self.shelf_set.all():
            shelf.delete()
        return super().delete(*args, **kwargs)

class Shelf(models.Model):
    name = models.CharField(max_length=20, verbose_name='Название')
    private = models.BooleanField(default=True, verbose_name='Тип полки', 
                                  choices=[(True, 'Частная (видна только Вам)'), (False, 'Открытая (видна всем)')])
    owner = models.ForeignKey(BookUser, on_delete=models.CASCADE, verbose_name='Владелец')

    class Meta:
        ordering = ['id']
        verbose_name = 'Полка'
        verbose_name_plural = 'Полки'

    def __str__(self):
        return self.name
    
    def delete(self, *args, **kwargs):
        for element in self.shelfrecord_set.all():
            element.delete()
        return super().delete(*args, **kwargs)

class ShelfRecord(models.Model):
    title = models.CharField(max_length=250, verbose_name='Название')
    author = models.CharField(max_length=250, verbose_name='Автор')
    comment = models.TextField(verbose_name='Комментарий', default='', blank=True)
    rating = models.SmallIntegerField(default=0, verbose_name='Оценка')
    read_date = models.DateField(db_index=True, verbose_name='Дата')
    cover = models.ImageField(upload_to=get_covers_upload_path, null=True, blank=True, verbose_name='Обложка')
    shelf = models.ForeignKey(Shelf, on_delete=models.CASCADE, verbose_name='Полка')
    random_cover = models.SmallIntegerField(default=0, verbose_name='Случайная обложка')
    
    class Meta:
        ordering = ['-read_date']
        verbose_name = 'Элемент полки'
        verbose_name_plural = 'Элементы полки'

    def __str__(self):
        return self.title