from django.urls import path

from .views import users_view, shelfs_view, records_view, records_add

app_name = 'hs'

urlpatterns = [
    path('users/', users_view),
    path('shelfs/', shelfs_view),
    path('shelf/<int:shelf_pk>/', records_view),
    path('records/add/', records_add),
]