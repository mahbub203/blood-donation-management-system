from django.contrib import admin
from donors.models import DonorProfile


@admin.register(DonorProfile)
class DonorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'blood_group', 'gender', 'district', 'upazila', 'is_available', 'last_donation_date', 'total_donations')
    list_filter = ('blood_group', 'gender', 'is_available', 'district__division', 'district')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__phone_number', 'district__name')
