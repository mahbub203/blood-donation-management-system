from django.contrib import admin
from core.models import District, Upazila, BloodGroup, BloodCompatibility


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'division', 'bn_name', 'created_at')
    list_filter = ('division',)
    search_fields = ('name', 'bn_name')


@admin.register(Upazila)
class UpazilaAdmin(admin.ModelAdmin):
    list_display = ('name', 'district', 'bn_name')
    list_filter = ('district__division', 'district')
    search_fields = ('name', 'district__name')


@admin.register(BloodGroup)
class BloodGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'antigen', 'antibody', 'description')
    search_fields = ('name',)


@admin.register(BloodCompatibility)
class BloodCompatibilityAdmin(admin.ModelAdmin):
    list_display = ('donor_group', 'recipient_group', 'notes')
    list_filter = ('donor_group', 'recipient_group')
