from django.urls import path
from hospitals import views

app_name = 'hospitals'

urlpatterns = [
    path('dashboard/', views.hospital_dashboard, name='dashboard'),
]
