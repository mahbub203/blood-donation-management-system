from django.urls import path
from donors import views

app_name = 'donors'

urlpatterns = [
    path('search/', views.donor_search, name='search'),
    path('dashboard/', views.donor_dashboard, name='dashboard'),
    path('toggle-availability/', views.toggle_availability, name='toggle_availability'),
    path('history/', views.donation_history, name='history'),
]
