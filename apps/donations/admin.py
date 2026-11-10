from django.contrib import admin
from donations.models import Donation, DonationAppointment


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('donation_code', 'donor', 'blood_group', 'donation_date', 'donation_location', 'units_donated', 'status', 'verified_by')
    list_filter = ('blood_group', 'status', 'donation_date')
    search_fields = ('donation_code', 'donor__user__username', 'donor__user__first_name', 'donation_location')


@admin.register(DonationAppointment)
class DonationAppointmentAdmin(admin.ModelAdmin):
    list_display = ('donor', 'blood_request', 'appointment_date', 'appointment_time', 'status')
    list_filter = ('status', 'appointment_date')
    search_fields = ('donor__user__username', 'blood_request__request_code', 'blood_request__patient_name')
