from django.urls import path
from blood_requests import views

app_name = 'blood_requests'

urlpatterns = [
    path('', views.request_list, name='list'),
    path('create/', views.request_create, name='create'),
    path('my-requests/', views.my_requests, name='my_requests'),
    path('<int:request_id>/', views.request_detail, name='detail'),
    path('<int:request_id>/cancel/', views.request_cancel, name='cancel'),
]
