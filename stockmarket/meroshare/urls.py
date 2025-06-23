from django.urls import path
from . import views

app_name = 'meroshare'

urlpatterns = [
    path('', views.account_list, name='account_list'),
    path('create/', views.account_create, name='account_create'),
    path('update/<int:pk>/', views.account_update, name='account_update'),
    path('delete/<int:pk>/', views.account_delete, name='account_delete'),
    path('account/<int:pk>/toggle-auto-ipo/', views.toggle_auto_ipo, name='toggle_auto_ipo'),
]
