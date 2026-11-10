from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from datetime import date
from core.models import District, BloodGroup
from blood_requests.models import BloodRequest
from donors.models import DonorProfile
from donations.models import Donation, DonationAppointment

User = get_user_model()


class DonationManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.district = District.objects.create(name='Dhaka', division='Dhaka')
        self.blood_group = BloodGroup.objects.create(name='A+')

        self.admin = User.objects.create_superuser(
            username='admin_don',
            phone_number='+8801744444441',
            role=User.Role.ADMIN
        )

        self.donor_user = User.objects.create_user(
            username='donor_don',
            phone_number='+8801744444442',
            role=User.Role.DONOR
        )
        self.donor_profile = DonorProfile.objects.create(
            user=self.donor_user,
            blood_group=self.blood_group,
            gender='M',
            date_of_birth=date(1996, 5, 5),
            district=self.district,
            full_address='Uttara',
            is_available=True,
            total_donations=0
        )

        self.requester = User.objects.create_user(
            username='req_don',
            phone_number='+8801744444443',
            role=User.Role.REQUESTER
        )
        self.blood_request = BloodRequest.objects.create(
            requester=self.requester,
            patient_name='Surgery Patient',
            blood_group=self.blood_group,
            units_needed=1,
            hospital_name='Apollo Hospital',
            hospital_address='Bashundhara',
            district=self.district,
            required_date=date.today(),
            emergency_level='URGENT',
            contact_number='+8801744444443',
            description='Needed for surgical procedure',
            status=BloodRequest.Status.APPROVED
        )

    def test_certify_completed_donation_updates_all_records(self):
        donation = Donation.objects.create(
            donor=self.donor_profile,
            blood_request=self.blood_request,
            donation_date=date.today(),
            donation_location='Apollo Hospital Blood Bank',
            blood_group=self.blood_group,
            units_donated=1,
            status=Donation.Status.SCHEDULED
        )

        self.client.force_login(self.admin)
        resp = self.client.post(
            reverse('donations:certify', kwargs={'donation_id': donation.id}),
            {'remarks': 'Transfusion successfully verified'}
        )
        self.assertEqual(resp.status_code, 302)

        donation.refresh_from_db()
        self.assertEqual(donation.status, Donation.Status.COMPLETED)
        self.assertEqual(donation.verified_by, self.admin)

        self.donor_profile.refresh_from_db()
        self.assertEqual(self.donor_profile.last_donation_date, date.today())
        self.assertEqual(self.donor_profile.total_donations, 1)

        self.blood_request.refresh_from_db()
        self.assertEqual(self.blood_request.status, BloodRequest.Status.FULFILLED)

    def test_database_constraint_prevents_duplicate_completed_donation_same_day(self):
        Donation.objects.create(
            donor=self.donor_profile,
            donation_date=date.today(),
            donation_location='Hospital 1',
            blood_group=self.blood_group,
            units_donated=1,
            status=Donation.Status.COMPLETED
        )

        # Attempt to insert a second COMPLETED donation on the same date for the same donor
        with self.assertRaises(IntegrityError):
            Donation.objects.create(
                donor=self.donor_profile,
                donation_date=date.today(),
                donation_location='Hospital 2',
                blood_group=self.blood_group,
                units_donated=1,
                status=Donation.Status.COMPLETED
            )
