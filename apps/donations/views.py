from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, connection
from datetime import date
from donations.models import Donation, DonationAppointment
from blood_requests.models import BloodRequest
from donors.models import DonorProfile
from core.models import BloodGroup
from hospitals.models import HospitalOrganization
from notifications.models import Notification
from analytics.models import ActivityLog


@login_required
def schedule_appointment(request, request_id):
    """
    Allows an eligible donor to schedule a donation appointment for a specific blood request.
    """
    if not request.user.is_donor_role:
        messages.error(request, "Only registered blood donors can schedule donation appointments.")
        return redirect('blood_requests:detail', request_id=request_id)

    blood_request = get_object_or_404(BloodRequest, id=request_id)
    donor_profile = request.user.donor_profile

    if not donor_profile.is_available:
        messages.warning(request, "Your status is set to Unavailable. Please update availability in your dashboard.")
        return redirect('donors:dashboard')

    if request.method == 'POST':
        appt_date = request.POST.get('appointment_date')
        appt_time = request.POST.get('appointment_time')
        notes = request.POST.get('notes', '')

        if not appt_date or not appt_time:
            messages.error(request, "Please specify both appointment date and preferred time.")
            return redirect('donations:schedule', request_id=request_id)

        with transaction.atomic():
            appointment = DonationAppointment.objects.create(
                donor=donor_profile,
                blood_request=blood_request,
                appointment_date=appt_date,
                appointment_time=appt_time,
                notes=notes,
                status='SCHEDULED'
            )

            # Update request status to DONOR_FOUND if still APPROVED/PENDING
            if blood_request.status in [BloodRequest.Status.PENDING, BloodRequest.Status.APPROVED]:
                blood_request.status = BloodRequest.Status.DONOR_FOUND
                blood_request.save()

            # Create scheduled Donation placeholder
            Donation.objects.create(
                donor=donor_profile,
                blood_request=blood_request,
                donation_date=appt_date,
                donation_location=f"{blood_request.hospital_name}, {blood_request.district.name}",
                blood_group=donor_profile.blood_group,
                units_donated=1,
                status=Donation.Status.SCHEDULED,
                remarks=f"Scheduled donation for patient {blood_request.patient_name}"
            )

            # Notify requester
            Notification.send(
                user=blood_request.requester,
                title="Donor Found for Blood Request!",
                message=f"Donor {request.user.get_full_name() or request.user.username} has scheduled to donate on {appt_date} at {appt_time}.",
                notification_type=Notification.Type.REQUEST,
                link=f"/requests/{blood_request.id}/"
            )

            ActivityLog.log(
                action="APPOINTMENT_SCHEDULED",
                user=request.user,
                details=f"Scheduled donation for request {blood_request.request_code} on {appt_date}"
            )

        messages.success(request, "Appointment successfully scheduled! The requester and hospital have been notified.")
        return redirect('donors:dashboard')

    context = {
        'req': blood_request,
        'profile': donor_profile,
    }
    return render(request, 'donations/schedule.html', context)


@login_required
def certify_donation(request, donation_id):
    """
    Privileged Action: Authorized Admin or Verified Hospital certifies a completed donation.
    Executes PostgreSQL Stored Function fn_certify_completed_donation() or atomic ORM transaction.
    """
    if not (request.user.is_admin_role or request.user.is_hospital_role):
        messages.error(request, "Only Administrators and Verified Hospitals can certify donations.")
        return redirect('core:home')

    donation = get_object_or_404(Donation, id=donation_id)

    if donation.status == Donation.Status.COMPLETED:
        messages.info(request, "This donation is already marked as completed.")
        return redirect('analytics:admin_dashboard')

    remarks = request.POST.get('remarks', 'Certified and transfused successfully.')

    # Demonstrate execution of PostgreSQL Stored Function fn_certify_completed_donation
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT fn_certify_completed_donation(%s, %s, %s);",
                [donation.id, request.user.id, remarks]
            )
            result = cursor.fetchone()[0]

        messages.success(request, f"Donation [{donation.donation_code}] certified via PostgreSQL stored function! Donor record updated.")
    except Exception as e:
        # Fallback to atomic ORM transaction if stored function encounter parameter issues
        with transaction.atomic():
            donation.status = Donation.Status.COMPLETED
            donation.verified_by = request.user
            donation.remarks = f"{donation.remarks} | {remarks}".strip(' | ')
            donation.save()

            dp = donation.donor
            dp.last_donation_date = donation.donation_date
            dp.total_donations += 1
            dp.save()

            if donation.blood_request:
                donation.blood_request.status = BloodRequest.Status.FULFILLED
                donation.blood_request.save()

            ActivityLog.log(action="DONATION_CERTIFIED", user=request.user, details=f"Certified donation {donation.donation_code}")
        messages.success(request, f"Donation [{donation.donation_code}] certified successfully!")

    # Notify donor of certificate and appreciation
    Notification.send(
        user=donation.donor.user,
        title="Donation Certified - Thank You!",
        message=f"Your whole blood donation on {donation.donation_date} has been officially verified. You saved a life today!",
        notification_type=Notification.Type.DONATION,
        link="/donors/history/"
    )

    if request.user.is_admin_role:
        return redirect('analytics:admin_donations')
    return redirect('hospitals:dashboard')


@login_required
def record_donation_direct(request):
    """
    Allows Admins and Verified Hospitals to record direct/walk-in or blood camp donations.
    """
    if not (request.user.is_admin_role or request.user.is_hospital_role):
        messages.error(request, "Unauthorized access.")
        return redirect('core:home')

    if request.method == 'POST':
        donor_id = request.POST.get('donor_id')
        donation_date = request.POST.get('donation_date')
        location = request.POST.get('donation_location')
        units = int(request.POST.get('units_donated', 1))
        remarks = request.POST.get('remarks', '')

        donor_profile = get_object_or_404(DonorProfile, id=donor_id)

        # Integrity check: Check if donor already has completed donation on this date
        if Donation.objects.filter(donor=donor_profile, donation_date=donation_date, status=Donation.Status.COMPLETED).exists():
            messages.error(request, "Integrity constraint: This donor already has a recorded completed donation on this date.")
            return redirect('donations:record_direct')

        with transaction.atomic():
            donation = Donation.objects.create(
                donor=donor_profile,
                donation_date=donation_date,
                donation_location=location,
                blood_group=donor_profile.blood_group,
                units_donated=units,
                status=Donation.Status.COMPLETED,
                verified_by=request.user,
                remarks=remarks
            )

            donor_profile.last_donation_date = donation_date
            donor_profile.total_donations += 1
            donor_profile.save()

            ActivityLog.log(
                action="DIRECT_DONATION_RECORDED",
                user=request.user,
                details=f"Recorded {units} unit(s) for donor {donor_profile.user.get_full_name()} at {location}"
            )

        messages.success(request, f"Donation [{donation.donation_code}] successfully recorded and verified!")
        if request.user.is_admin_role:
            return redirect('analytics:admin_donations')
        return redirect('hospitals:dashboard')

    donors = DonorProfile.objects.select_related('user', 'blood_group', 'district').filter(is_available=True)
    return render(request, 'donations/record_direct.html', {'donors': donors})
