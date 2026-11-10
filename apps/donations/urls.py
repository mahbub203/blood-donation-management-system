from django.urls import path
from donations import views

app_name = 'donations'

urlpatterns = [
    path('schedule/<int:request_id>/', views.schedule_appointment, name='schedule'),
    path('certify/<int:donation_id>/', views.certify_donation, name='certify'),
    path('record-direct/', views.record_donation_direct, name='record_direct'),
]
