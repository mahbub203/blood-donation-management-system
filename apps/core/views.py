from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count, Q
from core.models import District, Upazila, BloodGroup, BloodCompatibility
from donors.models import DonorProfile
from blood_requests.models import BloodRequest
from donations.models import Donation
from hospitals.models import HospitalOrganization


def home(request):
    """
    Public landing page featuring live database metrics, urgent blood requests,
    and rapid search filters.
    """
    # Real-time KPIs
    total_donors = DonorProfile.objects.count()
    available_donors = DonorProfile.objects.filter(is_available=True).count()
    total_requests = BloodRequest.objects.count()
    fulfilled_requests = BloodRequest.objects.filter(status=BloodRequest.Status.FULFILLED).count()
    verified_hospitals = HospitalOrganization.objects.filter(is_verified=True).count()
    total_units_donated = Donation.objects.filter(status=Donation.Status.COMPLETED).count()

    # Active urgent/critical blood requests
    urgent_requests = BloodRequest.objects.filter(
        status__in=[BloodRequest.Status.PENDING, BloodRequest.Status.APPROVED]
    ).select_related('blood_group', 'district', 'upazila').order_by(
        models_order_urgency(), '-created_at'
    )[:6]

    districts = District.objects.all().order_by('name')
    blood_groups = BloodGroup.objects.all()

    context = {
        'total_donors': total_donors,
        'available_donors': available_donors,
        'total_requests': total_requests,
        'fulfilled_requests': fulfilled_requests,
        'verified_hospitals': verified_hospitals,
        'total_units_donated': total_units_donated,
        'urgent_requests': urgent_requests,
        'districts': districts,
        'blood_groups': blood_groups,
    }
    return render(request, 'core/home.html', context)


def models_order_urgency():
    """Helper to sort CRITICAL before URGENT before NORMAL."""
    from django.db.models import Case, When, Value, IntegerField
    return Case(
        When(emergency_level=BloodRequest.EmergencyLevel.CRITICAL, then=Value(1)),
        When(emergency_level=BloodRequest.EmergencyLevel.URGENT, then=Value(2)),
        default=Value(3),
        output_field=IntegerField(),
    )


def about(request):
    """About Us page outlining project mission and medical advisory."""
    return render(request, 'core/about.html')


def how_it_works(request):
    """Educational walkthrough of blood donation workflow and compatibility."""
    compatibilities = BloodCompatibility.objects.select_related('donor_group', 'recipient_group').all()
    blood_groups = BloodGroup.objects.all()
    return render(request, 'core/how_it_works.html', {
        'compatibilities': compatibilities,
        'blood_groups': blood_groups
    })


def contact(request):
    """Contact & emergency support information."""
    return render(request, 'core/contact.html')


def api_upazilas(request):
    """
    AJAX endpoint returning list of upazilas for a district.
    """
    district_id = request.GET.get('district_id')
    if not district_id:
        return JsonResponse({'upazilas': []})

    upazilas = Upazila.objects.filter(district_id=district_id).values('id', 'name')
    return JsonResponse({'upazilas': list(upazilas)})
