from django.urls import path

from .views import index, user_logout, UserLoginView, RegisterUser, user_activate, register_done
from .views import ping, profile, ChangeUserInfoView, PasswordChangeView, DeleteUserView
from .views import UserPasswordResetView, UserPasswordResetDoneView, UserPasswordResetConfirmView
from .views import shelf_add, shelf_detail, record_add, shelf_change, shelf_delete, record_detail
from .views import record_change, record_delete, shelf_upload

app_name = 'main'

urlpatterns = [
    path('logout/', user_logout, name='logout'),
    path('shelf/add/<int:pk>/', record_add, name='record_add'),
    path('shelf/add/', shelf_add, name='shelf_add'),
    path('shelf/<int:pk>/', shelf_detail, name='shelf_detail'),
    path('shelf/upload/<int:pk>/', shelf_upload, name='shelf_upload'),
    path('shelf/change/<int:pk>/', shelf_change, name='shelf_change'),
    path('shelf/delete/<int:pk>/', shelf_delete, name='shelf_delete'),
    path('shelf/record/change/<int:pk>/', record_change, name='record_change'),
    path('shelf/record/delete/<int:pk>/', record_delete, name='record_delete'),
    path('shelf/record/<int:pk>/', record_detail, name='record_detail'),
    path('profile/password/reset_done/', UserPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('profile/password/reset/<uidb64>/<token>/', UserPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('profile/password/reset/', UserPasswordResetView.as_view(), name='password_reset'),
    path('profile/password/change/', PasswordChangeView.as_view(), name='password_change'),
    path('profile/change/', ChangeUserInfoView.as_view(), name='profile_change'),
    path('profile/delete/', DeleteUserView.as_view(), name='delete_user'),
    path('profile/', profile, name='profile'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('register/activate/<str:sign>/', user_activate, name='register_activate'),
    path('register/done/', register_done, name='register_done'),
    path('register/', RegisterUser.as_view(), name='register'),
    path('ping/', ping, name='ping'),
    path('', index, name='index')
]
