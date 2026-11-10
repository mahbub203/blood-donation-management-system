from django.contrib import admin
from blood_requests.models import BloodRequest, RequesterProfile


@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = ('request_code', 'patient_name', 'blood_group', 'units_needed', 'hospital_name', 'district', 'required_date', 'emergency_level', 'status')
    list_filter = ('blood_group', 'emergency_level', 'status', 'district')
    search_fields = ('request_code', 'patient_name', 'hospital_name', 'contact_number')


@admin.register(RequesterProfile)
class RequesterProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'district', 'upazila', 'alternate_phone')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'alternate_phone')
