from django.urls import path

from .views import index, user_logout, UserLoginView

app_name = 'main'

urlpatterns = [
    path('logout/', user_logout, name='logout'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('', index, name='index'),
]