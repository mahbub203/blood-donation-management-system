from django.urls import path
from analytics import views

app_name = 'analytics'

urlpatterns = [
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-users/', views.admin_users, name='admin_users'),
    path('admin-users/<int:user_id>/toggle/', views.admin_toggle_user_active, name='admin_toggle_user'),
    path('admin-requests/', views.admin_requests, name='admin_requests'),
    path('admin-requests/<int:request_id>/update-status/', views.admin_update_request_status, name='admin_update_request_status'),
    path('admin-donations/', views.admin_donations, name='admin_donations'),
    path('admin-hospitals/', views.admin_hospitals, name='admin_hospitals'),
    path('admin-hospitals/<int:hospital_id>/verify/', views.admin_verify_hospital, name='admin_verify_hospital'),
    path('admin-logs/', views.admin_activity_logs, name='admin_logs'),
    path('reports/', views.reports, name='reports'),
    path('reports/export/<str:report_type>/', views.export_csv, name='export_csv'),
    path('dbms-showcase/', views.dbms_showcase, name='dbms_showcase'),
]
