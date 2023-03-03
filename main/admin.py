from django.contrib import admin
from .models import BookUser

class BookUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'is_active', 'is_activated', 'is_superuser', 'last_login')
    list_display_links = ('username',)

admin.site.register(BookUser, BookUserAdmin)
