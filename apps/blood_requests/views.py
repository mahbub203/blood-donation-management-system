from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from datetime import date, timedelta
from core.models import District, Upazila, BloodGroup, BloodCompatibility
from blood_requests.models import BloodRequest
from blood_requests.forms import BloodRequestForm
from donors.models import DonorProfile
from notifications.models import Notification
from analytics.models import ActivityLog


def request_list(request):
    """Public searchable listing of blood donation requests."""
    blood_group_id = request.GET.get('blood_group')
    district_id = request.GET.get('district')
    emergency_level = request.GET.get('urgency')
    status = request.GET.get('status', '')

    requests_qs = BloodRequest.objects.select_related(
        'blood_group', 'district', 'upazila', 'requester'
    )

    if blood_group_id:
        requests_qs = requests_qs.filter(blood_group_id=blood_group_id)
    if district_id:
        requests_qs = requests_qs.filter(district_id=district_id)
    if emergency_level:
        requests_qs = requests_qs.filter(emergency_level=emergency_level)
    if status:
        requests_qs = requests_qs.filter(status=status)
    else:
        # Default: show active requests first
        requests_qs = requests_qs.filter(
            status__in=[
                BloodRequest.Status.PENDING,
                BloodRequest.Status.APPROVED,
                BloodRequest.Status.DONOR_FOUND
            ]
        )

    # Sort critical first, then required_date asc
    from django.db.models import Case, When, Value, IntegerField
    urgency_order = Case(
        When(emergency_level=BloodRequest.EmergencyLevel.CRITICAL, then=Value(1)),
        When(emergency_level=BloodRequest.EmergencyLevel.URGENT, then=Value(2)),
        default=Value(3),
        output_field=IntegerField()
    )
    blood_requests = requests_qs.order_by(urgency_order, 'required_date')[:50]

    districts = District.objects.all()
    blood_groups = BloodGroup.objects.all()

    context = {
        'blood_requests': blood_requests,
        'districts': districts,
        'blood_groups': blood_groups,
        'selected_bg_id': int(blood_group_id) if blood_group_id else None,
        'selected_district_id': int(district_id) if district_id else None,
        'selected_urgency': emergency_level,
        'selected_status': status,
        'total_count': requests_qs.count(),
    }
    return render(request, 'blood_requests/list.html', context)


def request_detail(request, request_id):
    """
    Detailed view of a blood request.
    Crucially: Computes and displays matching eligible donors who are ABO/Rh compatible!
    """
    blood_request = get_object_or_404(
        BloodRequest.objects.select_related('blood_group', 'district', 'upazila', 'requester'),
        id=request_id
    )

    # ABO/Rh compatibility: which donors can donate red cells to this request's blood group?
    compatible_donor_group_ids = BloodCompatibility.objects.filter(
        recipient_group=blood_request.blood_group
    ).values_list('donor_group_id', flat=True)

    # Query matching eligible donors in same district
    threshold_date = date.today() - timedelta(days=120)
    matching_donors = DonorProfile.objects.select_related(
        'user', 'blood_group', 'district', 'upazila'
    ).filter(
        blood_group_id__in=compatible_donor_group_ids,
        district=blood_request.district,
        is_available=True
    ).filter(
        Q(last_donation_date__isnull=True) | Q(last_donation_date__lte=threshold_date)
    ).order_by('-total_donations')[:20]

    # Check if user is the author or admin
    can_manage = False
    if request.user.is_authenticated:
        can_manage = (
            request.user == blood_request.requester or
            request.user.is_admin_role or
            request.user.is_hospital_role
        )

    context = {
        'req': blood_request,
        'matching_donors': matching_donors,
        'can_manage': can_manage,
    }
    return render(request, 'blood_requests/detail.html', context)


@login_required
def request_create(request):
    """Allows authenticated Requesters, Hospitals, or Admins to post a blood request."""
    if request.method == 'POST':
        form = BloodRequestForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                blood_request = form.save(commit=False)
                blood_request.requester = request.user
                # If created by Hospital or Admin, auto-approve; otherwise Pending verification
                if request.user.is_hospital_role or request.user.is_admin_role:
                    blood_request.status = BloodRequest.Status.APPROVED
                else:
                    blood_request.status = BloodRequest.Status.APPROVED  # Auto-approved for responsiveness

                blood_request.save()

                ActivityLog.log(
                    action="BLOOD_REQUEST_CREATED",
                    user=request.user,
                    details=f"Created request {blood_request.request_code} for {blood_request.patient_name} [{blood_request.blood_group.name}]"
                )

                # Send notifications to compatible donors in that district
                compatible_donor_groups = BloodCompatibility.objects.filter(
                    recipient_group=blood_request.blood_group
                ).values_list('donor_group_id', flat=True)

                nearby_donors = DonorProfile.objects.filter(
                    district=blood_request.district,
                    blood_group_id__in=compatible_donor_groups,
                    is_available=True
                ).select_related('user')[:10]

                for dp in nearby_donors:
                    Notification.send(
                        user=dp.user,
                        title=f"{blood_request.get_emergency_level_display()} {blood_request.blood_group.name} Blood Request",
                        message=f"Urgent requirement for {blood_request.patient_name} at {blood_request.hospital_name}, {blood_request.district.name}.",
                        notification_type=Notification.Type.DONOR_MATCH,
                        link=f"/requests/{blood_request.id}/"
                    )

            messages.success(request, f"Blood request [{blood_request.request_code}] submitted successfully!")
            return redirect('blood_requests:detail', request_id=blood_request.id)
    else:
        # Prepopulate contact number if user has phone
        initial = {'contact_number': request.user.phone_number}
        form = BloodRequestForm(initial=initial)

    return render(request, 'blood_requests/create.html', {'form': form})


@login_required
def my_requests(request):
    """Personal dashboard for Requesters showing all requests they submitted."""
    requests = BloodRequest.objects.filter(
        requester=request.user
    ).select_related('blood_group', 'district', 'upazila').order_by('-created_at')

    return render(request, 'blood_requests/my_requests.html', {'requests': requests})


@login_required
def request_cancel(request, request_id):
    """Cancels a pending or approved blood request."""
    blood_request = get_object_or_404(BloodRequest, id=request_id)
    if not (request.user == blood_request.requester or request.user.is_admin_role):
        messages.error(request, "You do not have permission to modify this request.")
        return redirect('blood_requests:detail', request_id=request_id)

    blood_request.status = BloodRequest.Status.CANCELLED
    blood_request.save()

    ActivityLog.log(
        action="REQUEST_CANCELLED",
        user=request.user,
        details=f"Request {blood_request.request_code} was cancelled by user."
    )
    messages.info(request, f"Blood request {blood_request.request_code} has been cancelled.")
    return redirect('blood_requests:detail', request_id=request_id)
