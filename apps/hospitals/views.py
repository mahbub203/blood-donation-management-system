from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from hospitals.models import HospitalOrganization
from blood_requests.models import BloodRequest
from donations.models import Donation, DonationAppointment


@login_required
def hospital_dashboard(request):
    """
    Hospital / Healthcare Organization Management Portal.
    Allows verified healthcare facilities in Bangladesh to create blood requests,
    coordinate transfusion appointments, and verify completed blood donations.
    """
    if not (request.user.is_hospital_role or request.user.is_admin_role):
        messages.error(request, "Only healthcare organizations can access the Hospital Portal.")
        return redirect('accounts:dashboard_redirect')

    try:
        hospital = request.user.hospital_profile
    except HospitalOrganization.DoesNotExist:
        messages.error(request, "Hospital organization profile not found.")
        return redirect('accounts:profile_view')

    # Hospital blood requests
    my_requests = BloodRequest.objects.filter(
        requester=request.user
    ).select_related('blood_group', 'district').order_by('-created_at')

    # Appointments scheduled at this hospital or district
    appointments = DonationAppointment.objects.filter(
        blood_request__in=my_requests
    ).select_related('donor', 'blood_request').order_by('-appointment_date')

    # Donations verified by this hospital user
    verified_donations = Donation.objects.filter(
        verified_by=request.user
    ).select_related('donor', 'blood_group').order_by('-donation_date')

    # Pending donations to certify
    pending_donations = Donation.objects.filter(
        blood_request__in=my_requests,
        status=Donation.Status.SCHEDULED
    ).select_related('donor', 'blood_group')

    context = {
        'hospital': hospital,
        'my_requests': my_requests,
        'appointments': appointments,
        'verified_donations': verified_donations,
        'pending_donations': pending_donations,
    }
    return render(request, 'hospitals/dashboard.html', context)
