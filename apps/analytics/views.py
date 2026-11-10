from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import connection
from django.db.models import Count, Sum, Q
import csv
from datetime import date, timedelta
from accounts.models import User
from donors.models import DonorProfile
from blood_requests.models import BloodRequest
from donations.models import Donation
from hospitals.models import HospitalOrganization
from core.models import District, BloodGroup
from analytics.models import ActivityLog


def is_admin(user):
    return user.is_authenticated and (user.is_admin_role or user.is_superuser)


@user_passes_test(is_admin)
def admin_dashboard(request):
    """
    Main Administrator Control Center.
    Aggregates platform KPIs, Chart.js datasets, and operational overviews.
    """
    # Core KPIs
    total_users = User.objects.count()
    total_donors = DonorProfile.objects.count()
    available_donors = DonorProfile.objects.filter(is_available=True).count()
    total_requests = BloodRequest.objects.count()
    pending_requests = BloodRequest.objects.filter(status=BloodRequest.Status.PENDING).count()
    completed_donations = Donation.objects.filter(status=Donation.Status.COMPLETED).count()
    verified_hospitals = HospitalOrganization.objects.filter(is_verified=True).count()
    pending_hospitals = HospitalOrganization.objects.filter(is_verified=False).count()

    # Chart 1: Blood Group Distribution
    blood_groups = BloodGroup.objects.annotate(
        donor_count=Count('donors')
    ).values('name', 'donor_count')
    bg_labels = [bg['name'] for bg in blood_groups]
    bg_data = [bg['donor_count'] for bg in blood_groups]

    # Chart 2: Request Status Distribution
    status_counts = BloodRequest.objects.values('status').annotate(count=Count('id'))
    status_map = {item['status']: item['count'] for item in status_counts}
    status_labels = ['Pending', 'Approved', 'Donor Found', 'Fulfilled', 'Cancelled']
    status_data = [
        status_map.get('PENDING', 0),
        status_map.get('APPROVED', 0),
        status_map.get('DONOR_FOUND', 0),
        status_map.get('FULFILLED', 0),
        status_map.get('CANCELLED', 0),
    ]

    # Chart 3: Top Districts by Donors
    top_districts = District.objects.annotate(
        donor_count=Count('donors')
    ).filter(donor_count__gt=0).order_by('-donor_count')[:6]
    district_labels = [d.name for d in top_districts]
    district_data = [d.donor_count for d in top_districts]

    # Recent items
    recent_requests = BloodRequest.objects.select_related('blood_group', 'district', 'requester').order_by('-created_at')[:5]
    recent_donations = Donation.objects.select_related('donor', 'blood_group').order_by('-created_at')[:5]
    recent_logs = ActivityLog.objects.select_related('user').order_by('-created_at')[:6]

    context = {
        'total_users': total_users,
        'total_donors': total_donors,
        'available_donors': available_donors,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'completed_donations': completed_donations,
        'verified_hospitals': verified_hospitals,
        'pending_hospitals': pending_hospitals,
        'bg_labels': bg_labels,
        'bg_data': bg_data,
        'status_labels': status_labels,
        'status_data': status_data,
        'district_labels': district_labels,
        'district_data': district_data,
        'recent_requests': recent_requests,
        'recent_donations': recent_donations,
        'recent_logs': recent_logs,
    }
    return render(request, 'analytics/admin_dashboard.html', context)


@user_passes_test(is_admin)
def admin_users(request):
    """User Management Controller with role-filtering and activation toggle."""
    role = request.GET.get('role')
    search = request.GET.get('q', '').strip()

    users = User.objects.all().order_by('-date_joined')
    if role:
        users = users.filter(role=role)
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(phone_number__icontains=search)
        )

    return render(request, 'analytics/admin_users.html', {'users': users, 'search': search, 'role': role})


@user_passes_test(is_admin)
def admin_toggle_user_active(request, user_id):
    """Toggles user account active/suspended state."""
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        messages.error(request, "You cannot deactivate your own administrative account.")
        return redirect('analytics:admin_users')

    target_user.is_active = not target_user.is_active
    target_user.save()
    status_str = "Activated" if target_user.is_active else "Suspended"
    messages.success(request, f"User '{target_user.username}' has been {status_str}.")
    return redirect('analytics:admin_users')


@user_passes_test(is_admin)
def admin_requests(request):
    """Request Management with one-click status transitions."""
    status = request.GET.get('status')
    blood_requests = BloodRequest.objects.select_related('blood_group', 'district', 'requester').all().order_by('-created_at')
    if status:
        blood_requests = blood_requests.filter(status=status)

    return render(request, 'analytics/admin_requests.html', {'requests': blood_requests, 'selected_status': status})


@user_passes_test(is_admin)
def admin_update_request_status(request, request_id):
    """Admin updates blood request status (e.g. APPROVED, REJECTED, FULFILLED)."""
    blood_request = get_object_or_404(BloodRequest, id=request_id)
    new_status = request.POST.get('status')
    if new_status in BloodRequest.Status.values:
        old_status = blood_request.status
        blood_request.status = new_status
        blood_request.save()
        messages.success(request, f"Request {blood_request.request_code} updated from {old_status} to {new_status}.")
    return redirect('analytics:admin_requests')


@user_passes_test(is_admin)
def admin_donations(request):
    """Donation Management with certification capabilities."""
    donations = Donation.objects.select_related('donor', 'blood_group', 'blood_request', 'verified_by').all().order_by('-donation_date')
    return render(request, 'analytics/admin_donations.html', {'donations': donations})


@user_passes_test(is_admin)
def admin_hospitals(request):
    """Organization Management with verification workflow."""
    hospitals = HospitalOrganization.objects.select_related('user', 'district').all().order_by('-created_at')
    return render(request, 'analytics/admin_hospitals.html', {'hospitals': hospitals})


@user_passes_test(is_admin)
def admin_verify_hospital(request, hospital_id):
    """Approves or revokes Hospital Organization authorization."""
    hospital = get_object_or_404(HospitalOrganization, id=hospital_id)
    hospital.is_verified = not hospital.is_verified
    if hospital.is_verified:
        hospital.verified_by = request.user
        hospital.verified_at = date.today()
    hospital.save()

    status_str = "Verified & Authorized" if hospital.is_verified else "Revoked / Unverified"
    ActivityLog.log(
        action="HOSPITAL_VERIFIED",
        user=request.user,
        details=f"Hospital {hospital.org_name} was marked as {status_str}"
    )
    messages.success(request, f"Hospital '{hospital.org_name}' is now {status_str}.")
    return redirect('analytics:admin_hospitals')


@user_passes_test(is_admin)
def admin_activity_logs(request):
    """System activity and database audit logs."""
    logs = ActivityLog.objects.select_related('user').all().order_by('-created_at')[:100]
    return render(request, 'analytics/admin_logs.html', {'logs': logs})


@user_passes_test(is_admin)
def reports(request):
    """
    Comprehensive System Reporting Module.
    Supports date range filtering, printable formatting, and CSV exports.
    """
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Date defaults (past 90 days)
    if not end_date:
        end_date = date.today().strftime('%Y-%m-%d')
    if not start_date:
        start_date = (date.today() - timedelta(days=90)).strftime('%Y-%m-%d')

    donations_qs = Donation.objects.filter(
        donation_date__gte=start_date,
        donation_date__lte=end_date,
        status=Donation.Status.COMPLETED
    )
    requests_qs = BloodRequest.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )

    total_donations = donations_qs.count()
    total_units = donations_qs.aggregate(total=Sum('units_donated'))['total'] or 0
    total_requests = requests_qs.count()
    fulfilled_requests = requests_qs.filter(status=BloodRequest.Status.FULFILLED).count()

    # Blood group breakdown in date range
    bg_breakdown = donations_qs.values('blood_group__name').annotate(
        count=Count('id'), units=Sum('units_donated')
    ).order_by('-units')

    # District breakdown in date range
    district_breakdown = requests_qs.values('district__name').annotate(
        req_count=Count('id')
    ).order_by('-req_count')[:10]

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_donations': total_donations,
        'total_units': total_units,
        'total_requests': total_requests,
        'fulfilled_requests': fulfilled_requests,
        'bg_breakdown': bg_breakdown,
        'district_breakdown': district_breakdown,
    }
    return render(request, 'analytics/reports.html', context)


@user_passes_test(is_admin)
def export_csv(request, report_type):
    """Generates and downloads CSV reports."""
    response = HttpResponse(content_type='text/csv')

    if report_type == 'donors':
        response['Content-Disposition'] = 'attachment; filename="lifedrop_donors.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Full Name', 'Blood Group', 'District', 'Upazila', 'Phone', 'Available', 'Last Donation', 'Total Donations'])
        donors = DonorProfile.objects.select_related('user', 'blood_group', 'district', 'upazila').all()
        for d in donors:
            writer.writerow([
                d.id,
                d.user.get_full_name(),
                d.blood_group.name,
                d.district.name if d.district else '',
                d.upazila.name if d.upazila else '',
                d.user.phone_number,
                d.is_available,
                d.last_donation_date or 'Never',
                d.total_donations
            ])
        return response

    elif report_type == 'requests':
        response['Content-Disposition'] = 'attachment; filename="lifedrop_blood_requests.csv"'
        writer = csv.writer(response)
        writer.writerow(['Request Code', 'Patient Name', 'Blood Group', 'Units Needed', 'Hospital', 'District', 'Required Date', 'Emergency Level', 'Status', 'Contact'])
        reqs = BloodRequest.objects.select_related('blood_group', 'district').all()
        for r in reqs:
            writer.writerow([
                r.request_code,
                r.patient_name,
                r.blood_group.name,
                r.units_needed,
                r.hospital_name,
                r.district.name,
                r.required_date,
                r.emergency_level,
                r.status,
                r.contact_number
            ])
        return response

    elif report_type == 'donations':
        response['Content-Disposition'] = 'attachment; filename="lifedrop_donations.csv"'
        writer = csv.writer(response)
        writer.writerow(['Donation Code', 'Donor', 'Blood Group', 'Date', 'Location', 'Units', 'Status', 'Verified By'])
        dons = Donation.objects.select_related('donor', 'blood_group', 'verified_by').all()
        for d in dons:
            writer.writerow([
                d.donation_code,
                d.donor.user.get_full_name(),
                d.blood_group.name,
                d.donation_date,
                d.donation_location,
                d.units_donated,
                d.status,
                d.verified_by.get_full_name() if d.verified_by else 'Unverified'
            ])
        return response

    return redirect('analytics:reports')


def dbms_showcase(request):
    """
    Dedicated Academic DBMS Showcase for university course evaluation.
    Executes live SQL queries, views, aggregations, subqueries, and EXPLAIN ANALYZE on PostgreSQL.
    """
    query_type = request.GET.get('query', 'view_donors')
    sql_query = ""
    columns = []
    rows = []
    explain_result = []

    if query_type == 'view_donors':
        sql_query = "SELECT donor_profile_id, full_name, blood_group, district_name, is_eligible, days_remaining FROM view_available_eligible_donors LIMIT 15;"
    elif query_type == 'view_requests':
        sql_query = "SELECT request_code, patient_name, blood_group, district_name, emergency_level, status, matching_eligible_donors_count FROM view_blood_request_summary LIMIT 15;"
    elif query_type == 'view_district_stats':
        sql_query = "SELECT district_name, division, total_donors, available_donors, total_requests, fulfilled_requests, total_units_donated FROM view_district_donation_stats ORDER BY total_donors DESC;"
    elif query_type == 'join_multi_table':
        sql_query = """
        SELECT 
            br.request_code,
            br.patient_name,
            bg.name AS blood_group,
            d.name AS district,
            u.first_name || ' ' || u.last_name AS requester_name,
            u.phone_number AS requester_phone,
            COUNT(don.id) AS fulfilled_donations_count
        FROM blood_requests_bloodrequest br
        INNER JOIN core_bloodgroup bg ON br.blood_group_id = bg.id
        INNER JOIN core_district d ON br.district_id = d.id
        INNER JOIN accounts_user u ON br.requester_id = u.id
        LEFT JOIN donations_donation don ON don.blood_request_id = br.id AND don.status = 'COMPLETED'
        GROUP BY br.id, br.request_code, br.patient_name, bg.name, d.name, u.first_name, u.last_name, u.phone_number
        ORDER BY br.created_at DESC;
        """.strip()
    elif query_type == 'subquery_unmatched':
        sql_query = """
        -- Donors who have never recorded a donation (Subquery demonstration)
        SELECT dp.id, u.first_name || ' ' || u.last_name AS donor_name, bg.name AS blood_group, d.name AS district
        FROM donors_donorprofile dp
        JOIN accounts_user u ON dp.user_id = u.id
        JOIN core_bloodgroup bg ON dp.blood_group_id = bg.id
        JOIN core_district d ON dp.district_id = d.id
        WHERE dp.id NOT IN (
            SELECT DISTINCT donor_id FROM donations_donation WHERE status = 'COMPLETED'
        );
        """.strip()
    elif query_type == 'explain_analyze':
        sql_query = "EXPLAIN ANALYZE SELECT * FROM view_available_eligible_donors WHERE blood_group = 'O+' AND district_name = 'Dhaka';"

    # Execute SQL in PostgreSQL
    with connection.cursor() as cursor:
        try:
            cursor.execute(sql_query)
            if cursor.description:
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
            else:
                rows = cursor.fetchall()
        except Exception as e:
            rows = []
            columns = ['Error']
            explain_result = [str(e)]

    context = {
        'query_type': query_type,
        'sql_query': sql_query,
        'columns': columns,
        'rows': rows,
    }
    return render(request, 'analytics/dbms_showcase.html', context)
