from django.contrib import admin
from hospitals.models import HospitalOrganization


@admin.register(HospitalOrganization)
class HospitalOrganizationAdmin(admin.ModelAdmin):
    list_display = ('org_name', 'org_type', 'license_number', 'district', 'contact_person', 'phone', 'is_verified')
    list_filter = ('org_type', 'is_verified', 'district')
    search_fields = ('org_name', 'license_number', 'contact_person', 'phone', 'email')
