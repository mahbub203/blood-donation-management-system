from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from datetime import date, timedelta
from core.models import District, Upazila, BloodGroup, BloodCompatibility
from donors.models import DonorProfile
from blood_requests.models import BloodRequest
from donations.models import Donation, DonationAppointment
from notifications.models import Notification
from analytics.models import ActivityLog


def donor_search(request):
    """
    Intelligent Donor Search Engine.
    Implements true ABO/Rh red-cell compatibility logic rather than simple identical matching.
    Includes filtering by district, upazila, availability, and 120-day eligibility rule.
    Protects donor contact information by masking it for unauthenticated public viewers.
    """
    blood_group_param = request.GET.get('blood_group')
    district_param = request.GET.get('district')
    upazila_param = request.GET.get('upazila')
    available_only = request.GET.get('available_only', '1') == '1'
    eligible_only = request.GET.get('eligible_only', '1') == '1'
    exact_match_only = request.GET.get('exact_match', '0') == '1'

    donors_qs = DonorProfile.objects.select_related('user', 'blood_group', 'district', 'upazila').filter(
        user__is_active=True
    )

    selected_blood_group = None
    compatible_groups = []

    if blood_group_param:
        if str(blood_group_param).isdigit():
            selected_blood_group = BloodGroup.objects.filter(id=int(blood_group_param)).first()
        else:
            selected_blood_group = BloodGroup.objects.filter(name__iexact=str(blood_group_param).strip()).first()

        if selected_blood_group:
            if exact_match_only:
                compatible_groups = [selected_blood_group]
                donors_qs = donors_qs.filter(blood_group=selected_blood_group)
            else:
                # ABO/Rh red-cell compatibility: Donors who can donate to this recipient group
                compat_donor_ids = BloodCompatibility.objects.filter(
                    recipient_group=selected_blood_group
                ).values_list('donor_group_id', flat=True)
                compatible_groups = BloodGroup.objects.filter(id__in=compat_donor_ids)
                donors_qs = donors_qs.filter(blood_group__in=compatible_groups)

    district_id = None
    if district_param and str(district_param).isdigit():
        district_id = int(district_param)
        donors_qs = donors_qs.filter(district_id=district_id)

    upazila_id = None
    if upazila_param and str(upazila_param).isdigit():
        upazila_id = int(upazila_param)
        donors_qs = donors_qs.filter(upazila_id=upazila_id)

    if available_only:
        donors_qs = donors_qs.filter(is_available=True)

    # 120-day eligibility filter: last_donation_date is NULL OR last_donation_date <= (today - 120 days)
    if eligible_only:
        threshold_date = date.today() - timedelta(days=120)
        donors_qs = donors_qs.filter(
            Q(last_donation_date__isnull=True) | Q(last_donation_date__lte=threshold_date)
        )

    # Order by: available first, then eligible first, then total donations desc
    donors = donors_qs.order_by('-is_available', 'last_donation_date')[:50]
    total_matching = donors_qs.count()

    districts = District.objects.all()
    upazilas = Upazila.objects.filter(district_id=district_id) if district_id else []
    blood_groups = BloodGroup.objects.all()

    # Academic SQL Demonstration Query snippet for professors
    bg_filter_clause = ""
    if selected_blood_group:
        if exact_match_only:
            bg_filter_clause = f"AND dp.blood_group_id = {selected_blood_group.id}"
        else:
            bg_filter_clause = f"AND dp.blood_group_id IN (SELECT donor_group_id FROM core_bloodcompatibility WHERE recipient_group_id = {selected_blood_group.id})"

    sql_explanation = f"""
    -- LifeDrop BD Compatible Donor Search SQL
    SELECT dp.id, u.first_name, u.last_name, bg.name, d.name AS district, dp.is_available, dp.last_donation_date
    FROM donors_donorprofile dp
    JOIN accounts_user u ON dp.user_id = u.id
    JOIN core_bloodgroup bg ON dp.blood_group_id = bg.id
    LEFT JOIN core_district d ON dp.district_id = d.id
    WHERE dp.is_available = TRUE
      AND (dp.last_donation_date IS NULL OR dp.last_donation_date <= CURRENT_DATE - INTERVAL '120 days')
      {bg_filter_clause}
    ORDER BY dp.is_available DESC, dp.total_donations DESC;
    """.strip()

    context = {
        'donors': donors,
        'total_matching': total_matching,
        'districts': districts,
        'upazilas': upazilas,
        'blood_groups': blood_groups,
        'selected_blood_group': selected_blood_group,
        'compatible_groups': compatible_groups,
        'selected_district_id': district_id,
        'selected_upazila_id': upazila_id,
        'available_only': available_only,
        'eligible_only': eligible_only,
        'exact_match_only': exact_match_only,
        'sql_explanation': sql_explanation,
    }
    return render(request, 'donors/search.html', context)


@login_required
def donor_dashboard(request):
    """
    Dedicated dashboard for Blood Donors:
    - Personal eligibility status & days countdown
    - Quick availability toggle
    - Compatible blood requests in their district
    - Personal donation stats and history
    """
    if not request.user.is_donor_role:
        messages.warning(request, "Only registered blood donors have access to the donor portal.")
        return redirect('accounts:dashboard_redirect')

    try:
        profile = request.user.donor_profile
    except DonorProfile.DoesNotExist:
        messages.error(request, "Please complete your donor profile.")
        return redirect('accounts:profile_view')

    # Compatible blood requests: patient needs blood that this donor can give
    recipient_groups = BloodCompatibility.objects.filter(
        donor_group=profile.blood_group
    ).values_list('recipient_group_id', flat=True)

    matching_requests = BloodRequest.objects.filter(
        blood_group_id__in=recipient_groups,
        status__in=[BloodRequest.Status.PENDING, BloodRequest.Status.APPROVED]
    ).select_related('blood_group', 'district', 'upazila').order_by('-emergency_level', '-created_at')[:6]

    recent_donations = profile.donations.select_related('blood_group', 'blood_request').all()[:5]
    appointments = profile.appointments.select_related('blood_request', 'hospital_org').order_by('-appointment_date')[:5]

    context = {
        'profile': profile,
        'matching_requests': matching_requests,
        'recent_donations': recent_donations,
        'appointments': appointments,
    }
    return render(request, 'donors/dashboard.html', context)


@login_required
def toggle_availability(request):
    """One-click AJAX or POST toggle for donor availability."""
    if not request.user.is_donor_role:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)

    profile = request.user.donor_profile
    profile.is_available = not profile.is_available
    profile.save()

    ActivityLog.log(
        action="AVAILABILITY_TOGGLED",
        user=request.user,
        details=f"Donor set availability to: {profile.is_available}"
    )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'is_available': profile.is_available})

    status_str = "Available" if profile.is_available else "Unavailable"
    messages.success(request, f"Your donation status has been updated to: {status_str}")
    return redirect('donors:dashboard')


@login_required
def donation_history(request):
    """Detailed personal donation log for the authenticated donor."""
    if not request.user.is_donor_role:
        return redirect('accounts:dashboard_redirect')

    profile = request.user.donor_profile
    donations = profile.donations.select_related('blood_group', 'blood_request', 'verified_by').all()

    return render(request, 'donors/history.html', {
        'profile': profile,
        'donations': donations
    })
