from django.contrib import admin
from analytics.models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'user', 'ip_address', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('action', 'details', 'user__username')
    readonly_fields = ('action', 'user', 'details', 'ip_address', 'created_at')
