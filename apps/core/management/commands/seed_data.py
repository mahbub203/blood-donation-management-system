from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from datetime import date, timedelta
from core.models import District, Upazila, BloodGroup, BloodCompatibility
from donors.models import DonorProfile
from blood_requests.models import BloodRequest, RequesterProfile
from hospitals.models import HospitalOrganization
from donations.models import Donation, DonationAppointment
from notifications.models import Notification
from analytics.models import ActivityLog

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds realistic Bangladesh-based demonstration data for LifeDrop BD'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Initiating LifeDrop BD comprehensive database seeding..."))

        with transaction.atomic():
            # 1. Seed Blood Groups
            blood_groups_data = [
                {'name': 'A+', 'antigen': 'A, Rh', 'antibody': 'Anti-B', 'description': 'Second most common group. Can receive A+, A-, O+, O-.'},
                {'name': 'A-', 'antigen': 'A', 'antibody': 'Anti-B', 'description': 'Can donate to A+, A-, AB+, AB-. Can receive A- and O-.'},
                {'name': 'B+', 'antigen': 'B, Rh', 'antibody': 'Anti-A', 'description': 'Highly prevalent in Bangladesh. Can receive B+, B-, O+, O-.'},
                {'name': 'B-', 'antigen': 'B', 'antibody': 'Anti-A', 'description': 'Rare. Can donate to B+, B-, AB+, AB-.'},
                {'name': 'AB+', 'antigen': 'A, B, Rh', 'antibody': 'None', 'description': 'Universal red cell recipient. Can receive all blood groups.'},
                {'name': 'AB-', 'antigen': 'A, B', 'antibody': 'None', 'description': 'Rare. Can receive from all Rh-negative groups.'},
                {'name': 'O+', 'antigen': 'Rh', 'antibody': 'Anti-A, Anti-B', 'description': 'Most common blood group. Can donate to all positive groups.'},
                {'name': 'O-', 'antigen': 'None', 'antibody': 'Anti-A, Anti-B', 'description': 'Universal red cell donor. Crucial in emergency trauma.'},
            ]

            bg_objs = {}
            for item in blood_groups_data:
                bg, _ = BloodGroup.objects.get_or_create(
                    name=item['name'],
                    defaults={
                        'antigen': item['antigen'],
                        'antibody': item['antibody'],
                        'description': item['description']
                    }
                )
                bg_objs[item['name']] = bg
            self.stdout.write(self.style.SUCCESS(f"Seeded {len(bg_objs)} Blood Groups."))

            # 2. Seed ABO/Rh Compatibility Matrix
            # Donor -> Recipients
            compatibility_map = {
                'O-': ['O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+'],
                'O+': ['O+', 'A+', 'B+', 'AB+'],
                'A-': ['A-', 'A+', 'AB-', 'AB+'],
                'A+': ['A+', 'AB+'],
                'B-': ['B-', 'B+', 'AB-', 'AB+'],
                'B+': ['B+', 'AB+'],
                'AB-': ['AB-', 'AB+'],
                'AB+': ['AB+'],
            }

            compat_count = 0
            for donor_code, rec_codes in compatibility_map.items():
                d_bg = bg_objs[donor_code]
                for r_code in rec_codes:
                    r_bg = bg_objs[r_code]
                    _, created = BloodCompatibility.objects.get_or_create(
                        donor_group=d_bg,
                        recipient_group=r_bg,
                        defaults={'notes': f'{donor_code} can safely donate red blood cells to {r_code}'}
                    )
                    if created:
                        compat_count += 1
            self.stdout.write(self.style.SUCCESS(f"Seeded {compat_count} Blood Compatibility pairs."))

            # 3. Seed Districts and Upazilas of Bangladesh
            geo_data = [
                ('Dhaka', 'Dhaka', 'ঢাকা', ['Dhanmondi', 'Mirpur', 'Gulshan', 'Uttara', 'Savar', 'Motijheel', 'Mohammadpur', 'Tejgaon']),
                ('Chittagong', 'Chittagong', 'চট্টগ্রাম', ['Panchlaish', 'Kotwali', 'Hathazari', 'Sitakunda', 'Patiya', 'Anwara']),
                ('Rajshahi', 'Rajshahi', 'রাজশাহী', ['Boalia', 'Motihar', 'Paba', 'Godagari', 'Bagmara', 'Charghat']),
                ('Khulna', 'Khulna', 'খুলনা', ['Kotwali', 'Sonadanga', 'Daulatpur', 'Khalishpur', 'Rupsha', 'Dumuria']),
                ('Barisal', 'Barisal', 'বরিশাল', ['Kotwali', 'Babuganj', 'Bakerganj', 'Banaripara', 'Gournadi']),
                ('Sylhet', 'Sylhet', 'সিলেট', ['Kotwali', 'South Surma', 'Beanibazar', 'Golapganj', 'Zakiganj']),
                ('Rangpur', 'Rangpur', 'রংপুর', ['Kotwali', 'Mithapukur', 'Pirganj', 'Badarganj', 'Gangachara']),
                ('Mymensingh', 'Mymensingh', 'ময়মনসিংহ', ['Kotwali', 'Muktagachha', 'Trishal', 'Bhaluka', 'Fulbaria']),
                ('Comilla', 'Chittagong', 'কুমিল্লা', ['Adarsha Sadar', 'Daudkandi', 'Chandina', 'Laksam']),
                ('Gazipur', 'Dhaka', 'গাজীপুর', ['Sadar', 'Tongi', 'Kaliakair', 'Kapasia']),
                ('Narayanganj', 'Dhaka', 'নারায়ণগঞ্জ', ['Sadar', 'Bandar', 'Rupganj', 'Araihazar']),
                ('Bogura', 'Rajshahi', 'বগুড়া', ['Sadar', 'Shajahanpur', 'Sherpur', 'Shibganj']),
            ]

            district_objs = {}
            upazila_objs = {}
            for dist_name, div, bn, upazilas in geo_data:
                dist, _ = District.objects.get_or_create(
                    name=dist_name,
                    defaults={'division': div, 'bn_name': bn}
                )
                district_objs[dist_name] = dist
                for uz_name in upazilas:
                    uz, _ = Upazila.objects.get_or_create(
                        district=dist,
                        name=uz_name,
                        defaults={'bn_name': uz_name}
                    )
                    upazila_objs[f"{dist_name}_{uz_name}"] = uz

            self.stdout.write(self.style.SUCCESS(f"Seeded {len(district_objs)} Districts & {len(upazila_objs)} Upazilas."))

            # 4. Seed Administrator
            admin_user, _ = User.objects.get_or_create(
                username='admin',
                defaults={
                    'email': 'admin@lifedropbd.org',
                    'first_name': 'System',
                    'last_name': 'Administrator',
                    'phone_number': '+8801700000000',
                    'role': User.Role.ADMIN,
                    'is_staff': True,
                    'is_superuser': True,
                    'is_verified': True,
                }
            )
            admin_user.set_password('Admin@12345')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created Superuser Admin (admin / Admin@12345)"))

            # 5. Seed Verified Hospitals / Organizations
            hospitals_data = [
                {
                    'username': 'hospital_dmch',
                    'email': 'bloodbank@dmch.gov.bd',
                    'name': 'Dhaka Medical College Hospital (DMCH)',
                    'org_type': HospitalOrganization.OrgType.HOSPITAL,
                    'license': 'DGHS-DMCH-1001',
                    'district': 'Dhaka',
                    'upazila': 'Dhanmondi',
                    'address': 'Secretariat Road, Ramna, Dhaka-1000',
                    'phone': '+8801711000101',
                    'contact': 'Prof. Dr. M. Rahman',
                },
                {
                    'username': 'hospital_bsmmu',
                    'email': 'transfusion@bsmmu.edu.bd',
                    'name': 'BSMMU Transfusion Medicine Department',
                    'org_type': HospitalOrganization.OrgType.HOSPITAL,
                    'license': 'DGHS-BSMMU-1002',
                    'district': 'Dhaka',
                    'upazila': 'Mohammadpur',
                    'address': 'Shahbag, Dhaka-1000',
                    'phone': '+8801711000102',
                    'contact': 'Dr. Sharmin Akter',
                },
                {
                    'username': 'hospital_cmch',
                    'email': 'bloodbank@cmch.gov.bd',
                    'name': 'Chittagong Medical College Hospital (CMCH)',
                    'org_type': HospitalOrganization.OrgType.HOSPITAL,
                    'license': 'DGHS-CMCH-2001',
                    'district': 'Chittagong',
                    'upazila': 'Panchlaish',
                    'address': '57 K.B. Fazlul Kader Road, Chittagong',
                    'phone': '+8801711000103',
                    'contact': 'Dr. Faruk Hossain',
                },
                {
                    'username': 'org_redcrescent',
                    'email': 'bloodprogram@bdrcs.org',
                    'name': 'Bangladesh Red Crescent Society Blood Center',
                    'org_type': HospitalOrganization.OrgType.BLOOD_BANK,
                    'license': 'DGHS-BDRCS-004',
                    'district': 'Dhaka',
                    'upazila': 'Mohammadpur',
                    'address': '7/5 Aurangzeb Road, Mohammadpur, Dhaka',
                    'phone': '+8801711000104',
                    'contact': 'Kamal Uddin (Director)',
                },
                {
                    'username': 'org_quantum',
                    'email': 'lab@quantummethod.org.bd',
                    'name': 'Quantum Foundation Blood Lab',
                    'org_type': HospitalOrganization.OrgType.BLOOD_BANK,
                    'license': 'DGHS-QF-009',
                    'district': 'Dhaka',
                    'upazila': 'Motijheel',
                    'address': '31/V Shilpacharya Zainul Abedin Sarak, Shantinagar, Dhaka',
                    'phone': '+8801711000105',
                    'contact': 'Nahid Parveen',
                },
            ]

            hospital_profiles = []
            for h_info in hospitals_data:
                user, _ = User.objects.get_or_create(
                    username=h_info['username'],
                    defaults={
                        'email': h_info['email'],
                        'first_name': h_info['name'][:30],
                        'phone_number': h_info['phone'],
                        'role': User.Role.HOSPITAL,
                        'is_verified': True,
                    }
                )
                user.set_password('Hospital@12345')
                user.save()

                dist = district_objs[h_info['district']]
                uz = upazila_objs.get(f"{h_info['district']}_{h_info['upazila']}")

                h_org, _ = HospitalOrganization.objects.get_or_create(
                    user=user,
                    defaults={
                        'org_name': h_info['name'],
                        'org_type': h_info['org_type'],
                        'license_number': h_info['license'],
                        'district': dist,
                        'upazila': uz,
                        'address': h_info['address'],
                        'contact_person': h_info['contact'],
                        'phone': h_info['phone'],
                        'email': h_info['email'],
                        'is_verified': True,
                        'verified_by': admin_user,
                        'verified_at': date.today(),
                    }
                )
                hospital_profiles.append(h_org)
            self.stdout.write(self.style.SUCCESS(f"Seeded {len(hospital_profiles)} Verified Hospitals/Organizations."))

            # 6. Seed Blood Donors (with varied eligibility: ready, recently donated, unavailable)
            donors_data = [
                {
                    'username': 'donor_tanvir',
                    'first_name': 'Tanvir',
                    'last_name': 'Ahmed',
                    'phone': '+8801712000001',
                    'blood': 'O+',
                    'gender': 'M',
                    'dob': date(1996, 5, 12),
                    'district': 'Dhaka',
                    'upazila': 'Dhanmondi',
                    'address': 'Road 27, Dhanmondi, Dhaka',
                    'last_donation': date.today() - timedelta(days=150),  # Eligible (>120 days)
                    'is_avail': True,
                    'donations': 4,
                },
                {
                    'username': 'donor_sadia',
                    'first_name': 'Sadia',
                    'last_name': 'Afrin',
                    'phone': '+8801712000002',
                    'blood': 'A+',
                    'gender': 'F',
                    'dob': date(1999, 8, 22),
                    'district': 'Dhaka',
                    'upazila': 'Mirpur',
                    'address': 'Section 10, Mirpur, Dhaka',
                    'last_donation': None,  # Eligible (First-time ready donor)
                    'is_avail': True,
                    'donations': 0,
                },
                {
                    'username': 'donor_rahim',
                    'first_name': 'Abdur',
                    'last_name': 'Rahim',
                    'phone': '+8801712000003',
                    'blood': 'O-',  # Universal donor
                    'gender': 'M',
                    'dob': date(1992, 11, 5),
                    'district': 'Chittagong',
                    'upazila': 'Panchlaish',
                    'address': 'GEC Circle, Chittagong',
                    'last_donation': date.today() - timedelta(days=200),  # Eligible
                    'is_avail': True,
                    'donations': 8,
                },
                {
                    'username': 'donor_karim',
                    'first_name': 'Karimul',
                    'last_name': 'Islam',
                    'phone': '+8801712000004',
                    'blood': 'B+',
                    'gender': 'M',
                    'dob': date(1994, 3, 14),
                    'district': 'Rajshahi',
                    'upazila': 'Boalia',
                    'address': 'Alupatti, Boalia, Rajshahi',
                    'last_donation': date.today() - timedelta(days=35),  # INELIGIBLE (<120 days)
                    'is_avail': True,
                    'donations': 3,
                },
                {
                    'username': 'donor_nusrat',
                    'first_name': 'Nusrat',
                    'last_name': 'Jahan',
                    'phone': '+8801712000005',
                    'blood': 'AB+',  # Universal recipient
                    'gender': 'F',
                    'dob': date(1998, 1, 29),
                    'district': 'Sylhet',
                    'upazila': 'Kotwali',
                    'address': 'Zindabazar, Sylhet',
                    'last_donation': date.today() - timedelta(days=130),  # Eligible
                    'is_avail': True,
                    'donations': 2,
                },
                {
                    'username': 'donor_arif',
                    'first_name': 'Ariful',
                    'last_name': 'Haq',
                    'phone': '+8801712000006',
                    'blood': 'A-',
                    'gender': 'M',
                    'dob': date(1991, 7, 19),
                    'district': 'Khulna',
                    'upazila': 'Sonadanga',
                    'address': 'Sonadanga Bus Stand Road, Khulna',
                    'last_donation': date.today() - timedelta(days=180),  # Eligible
                    'is_avail': True,
                    'donations': 5,
                },
                {
                    'username': 'donor_farhana',
                    'first_name': 'Farhana',
                    'last_name': 'Yesmin',
                    'phone': '+8801712000007',
                    'blood': 'B-',
                    'gender': 'F',
                    'dob': date(1997, 10, 3),
                    'district': 'Barisal',
                    'upazila': 'Kotwali',
                    'address': 'Sadarmukhi, Barisal',
                    'last_donation': date.today() - timedelta(days=140),  # Eligible
                    'is_avail': False,  # Temporarily unavailable
                    'donations': 2,
                },
                {
                    'username': 'donor_hasan',
                    'first_name': 'Mahmudul',
                    'last_name': 'Hasan',
                    'phone': '+8801712000008',
                    'blood': 'AB-',
                    'gender': 'M',
                    'dob': date(1995, 4, 18),
                    'district': 'Rangpur',
                    'upazila': 'Kotwali',
                    'address': 'Jahaj Company Mor, Rangpur',
                    'last_donation': None,  # Eligible
                    'is_avail': True,
                    'donations': 0,
                },
                {
                    'username': 'donor_mehedi',
                    'first_name': 'Mehedi',
                    'last_name': 'Hasan',
                    'phone': '+8801712000009',
                    'blood': 'O+',
                    'gender': 'M',
                    'dob': date(1993, 9, 9),
                    'district': 'Dhaka',
                    'upazila': 'Gulshan',
                    'address': 'Gulshan 2, Dhaka',
                    'last_donation': date.today() - timedelta(days=160),  # Eligible
                    'is_avail': True,
                    'donations': 6,
                },
                {
                    'username': 'donor_tania',
                    'first_name': 'Tania',
                    'last_name': 'Sultana',
                    'phone': '+8801712000010',
                    'blood': 'A+',
                    'gender': 'F',
                    'dob': date(2000, 2, 11),
                    'district': 'Dhaka',
                    'upazila': 'Uttara',
                    'address': 'Sector 7, Uttara, Dhaka',
                    'last_donation': date.today() - timedelta(days=70),  # Ineligible (<120 days)
                    'is_avail': True,
                    'donations': 1,
                },
            ]

            donor_profiles = []
            for d in donors_data:
                user, _ = User.objects.get_or_create(
                    username=d['username'],
                    defaults={
                        'email': f"{d['username']}@example.com",
                        'first_name': d['first_name'],
                        'last_name': d['last_name'],
                        'phone_number': d['phone'],
                        'role': User.Role.DONOR,
                        'is_verified': True,
                    }
                )
                user.set_password('Donor@12345')
                user.save()

                dist = district_objs[d['district']]
                uz = upazila_objs.get(f"{d['district']}_{d['upazila']}")
                bg = bg_objs[d['blood']]

                dp, _ = DonorProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'blood_group': bg,
                        'gender': d['gender'],
                        'date_of_birth': d['dob'],
                        'district': dist,
                        'upazila': uz,
                        'full_address': d['address'],
                        'last_donation_date': d['last_donation'],
                        'is_available': d['is_avail'],
                        'emergency_contact': '+8801812999999',
                        'bio': f"Committed blood donor from {dist.name}. Ready to assist in emergencies.",
                        'total_donations': d['donations'],
                    }
                )
                donor_profiles.append(dp)
            self.stdout.write(self.style.SUCCESS(f"Seeded {len(donor_profiles)} Donor Profiles."))

            # 7. Seed Requesters
            requesters_data = [
                {
                    'username': 'requester_kamal',
                    'first_name': 'Kamal',
                    'last_name': 'Hossain',
                    'phone': '+8801713000001',
                    'district': 'Dhaka',
                    'upazila': 'Dhanmondi',
                    'address': 'Dhanmondi 32, Dhaka',
                },
                {
                    'username': 'requester_monira',
                    'first_name': 'Monira',
                    'last_name': 'Begum',
                    'phone': '+8801713000002',
                    'district': 'Dhaka',
                    'upazila': 'Mohammadpur',
                    'address': 'Salimullah Road, Mohammadpur',
                },
                {
                    'username': 'requester_kabir',
                    'first_name': 'Kabir',
                    'last_name': 'Chowdhury',
                    'phone': '+8801713000003',
                    'district': 'Chittagong',
                    'upazila': 'Panchlaish',
                    'address': 'Nasirabad Housing, Chittagong',
                },
                {
                    'username': 'requester_tariq',
                    'first_name': 'Tariq',
                    'last_name': 'Anowar',
                    'phone': '+8801713000004',
                    'district': 'Rajshahi',
                    'upazila': 'Boalia',
                    'address': 'Shaheb Bazar, Rajshahi',
                },
            ]

            requester_users = []
            for r in requesters_data:
                user, _ = User.objects.get_or_create(
                    username=r['username'],
                    defaults={
                        'email': f"{r['username']}@example.com",
                        'first_name': r['first_name'],
                        'last_name': r['last_name'],
                        'phone_number': r['phone'],
                        'role': User.Role.REQUESTER,
                        'is_verified': True,
                    }
                )
                user.set_password('Requester@12345')
                user.save()

                dist = district_objs[r['district']]
                uz = upazila_objs.get(f"{r['district']}_{r['upazila']}")

                RequesterProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'district': dist,
                        'upazila': uz,
                        'address': r['address'],
                    }
                )
                requester_users.append(user)
            self.stdout.write(self.style.SUCCESS(f"Seeded {len(requester_users)} Blood Requesters."))

            # 8. Seed Blood Requests across statuses and emergency levels
            requests_data = [
                {
                    'requester': requester_users[0],
                    'patient': 'Rafiqul Islam (Age 52)',
                    'blood': 'O+',
                    'units': 2,
                    'hospital': 'Dhaka Medical College Hospital',
                    'address': 'Ward 14, Bed 8, DMCH, Dhaka',
                    'district': 'Dhaka',
                    'upazila': 'Dhanmondi',
                    'required_date': date.today() + timedelta(days=1),
                    'urgency': BloodRequest.EmergencyLevel.CRITICAL,
                    'contact': '+8801713000001',
                    'desc': 'Emergency cardiac bypass surgery scheduled for tomorrow morning. Need 2 units O+ blood urgently.',
                    'status': BloodRequest.Status.APPROVED,
                },
                {
                    'requester': requester_users[1],
                    'patient': 'Ayesha Begum (Age 34)',
                    'blood': 'A-',
                    'units': 1,
                    'hospital': 'BSMMU Hospital',
                    'address': 'Cabin 502, Block C, BSMMU, Shahbag, Dhaka',
                    'district': 'Dhaka',
                    'upazila': 'Mohammadpur',
                    'required_date': date.today() + timedelta(days=2),
                    'urgency': BloodRequest.EmergencyLevel.URGENT,
                    'contact': '+8801713000002',
                    'desc': 'C-section delivery patient with severe anemia. Requires 1 unit of A- negative blood.',
                    'status': BloodRequest.Status.PENDING,
                },
                {
                    'requester': requester_users[2],
                    'patient': 'Baby of Kabir (Newborn)',
                    'blood': 'B+',
                    'units': 1,
                    'hospital': 'Chittagong Medical College Hospital',
                    'address': 'NICU Unit, CMCH, Chittagong',
                    'district': 'Chittagong',
                    'upazila': 'Panchlaish',
                    'required_date': date.today() + timedelta(days=3),
                    'urgency': BloodRequest.EmergencyLevel.NORMAL,
                    'contact': '+8801713000003',
                    'desc': 'Neonatal jaundice and high bilirubin. Exchange transfusion scheduled.',
                    'status': BloodRequest.Status.DONOR_FOUND,
                },
                {
                    'requester': requester_users[3],
                    'patient': 'Tariqul Alam (Age 28)',
                    'blood': 'O-',
                    'units': 2,
                    'hospital': 'Rajshahi Medical College Hospital',
                    'address': 'Surgery Ward, RMCH, Rajshahi',
                    'district': 'Rajshahi',
                    'upazila': 'Boalia',
                    'required_date': date.today() - timedelta(days=5),
                    'urgency': BloodRequest.EmergencyLevel.CRITICAL,
                    'contact': '+8801713000004',
                    'desc': 'Road traffic accident with massive acute hemoperitoneum.',
                    'status': BloodRequest.Status.FULFILLED,
                },
            ]

            request_objs = []
            for req_info in requests_data:
                dist = district_objs[req_info['district']]
                uz = upazila_objs.get(f"{req_info['district']}_{req_info['upazila']}")
                bg = bg_objs[req_info['blood']]

                br = BloodRequest.objects.filter(
                    requester=req_info['requester'],
                    patient_name=req_info['patient'],
                    blood_group=bg
                ).first()

                if not br:
                    br = BloodRequest.objects.create(
                        requester=req_info['requester'],
                        patient_name=req_info['patient'],
                        blood_group=bg,
                        units_needed=req_info['units'],
                        hospital_name=req_info['hospital'],
                        hospital_address=req_info['address'],
                        district=dist,
                        upazila=uz,
                        required_date=req_info['required_date'],
                        emergency_level=req_info['urgency'],
                        contact_number=req_info['contact'],
                        description=req_info['desc'],
                        status=req_info['status'],
                    )
                request_objs.append(br)
            self.stdout.write(self.style.SUCCESS(f"Seeded {len(request_objs)} Blood Requests."))

            # 9. Seed Donations & Historical Records
            # Fulfilled donation for request_objs[3]
            donor_rahim = donor_profiles[2]  # O- universal donor
            don_date1 = date.today() - timedelta(days=5)
            if not Donation.objects.filter(donor=donor_rahim, donation_date=don_date1, status=Donation.Status.COMPLETED).exists():
                Donation.objects.create(
                    donor=donor_rahim,
                    blood_request=request_objs[3],
                    donation_date=don_date1,
                    donation_location='Rajshahi Medical College Blood Bank',
                    blood_group=bg_objs['O-'],
                    units_donated=1,
                    status=Donation.Status.COMPLETED,
                    verified_by=admin_user,
                    remarks='Successfully cross-matched and transfused for trauma surgery.'
                )

            # Historical completed donation
            donor_tanvir = donor_profiles[0]
            don_date2 = date.today() - timedelta(days=150)
            if not Donation.objects.filter(donor=donor_tanvir, donation_date=don_date2, status=Donation.Status.COMPLETED).exists():
                Donation.objects.create(
                    donor=donor_tanvir,
                    donation_date=don_date2,
                    donation_location='Dhaka Medical College Hospital',
                    blood_group=bg_objs['O+'],
                    units_donated=1,
                    status=Donation.Status.COMPLETED,
                    verified_by=admin_user,
                    remarks='Regular voluntary blood donation at DMCH blood bank camp.'
                )

            # Scheduled donation appointment
            donor_karim = donor_profiles[3]
            appt_date = date.today() + timedelta(days=3)
            if not DonationAppointment.objects.filter(donor=donor_karim, appointment_date=appt_date).exists():
                DonationAppointment.objects.create(
                    donor=donor_karim,
                    blood_request=request_objs[2],
                    hospital_org=hospital_profiles[2],
                    appointment_date=appt_date,
                    appointment_time='10:30:00',
                    status='SCHEDULED',
                    notes='Donor confirmed availability via phone call.'
                )
            self.stdout.write(self.style.SUCCESS("Seeded Donations & Appointments."))

            # 10. Seed In-App Notifications
            Notification.send(
                user=donor_tanvir.user,
                title="Critical O+ Blood Request in Dhaka",
                message="A critical blood request has been created at DMCH for patient Rafiqul Islam. Your blood group is compatible!",
                notification_type=Notification.Type.DONOR_MATCH,
                link=f"/requests/{request_objs[0].id}/"
            )
            Notification.send(
                user=requester_users[0],
                title="Blood Request Approved",
                message="Your blood request REQ-XXXX has been approved and matching donors are being notified.",
                notification_type=Notification.Type.REQUEST,
                link=f"/requests/{request_objs[0].id}/"
            )
            Notification.send(
                user=hospital_profiles[0].user,
                title="Hospital Profile Verified",
                message="Your hospital account has been verified by the LifeDrop BD administrator. You now have full access to blood transfusion management.",
                notification_type=Notification.Type.SYSTEM,
                link="/hospitals/dashboard/"
            )

            # 11. Seed Activity Logs
            ActivityLog.log(
                action="SYSTEM_INITIALIZED",
                user=admin_user,
                details="LifeDrop BD comprehensive database system initialized with seed data.",
                ip_address="127.0.0.1"
            )

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
