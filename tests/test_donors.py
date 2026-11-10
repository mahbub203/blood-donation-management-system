from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from core.models import District, Upazila, BloodGroup, BloodCompatibility
from donors.models import DonorProfile

User = get_user_model()


class DonorManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.district = District.objects.create(name='Dhaka', division='Dhaka')
        self.bg_o_neg = BloodGroup.objects.create(name='O-')
        self.bg_o_pos = BloodGroup.objects.create(name='O+')
        self.bg_ab_pos = BloodGroup.objects.create(name='AB+')

        # O- can donate to O- and O+
        BloodCompatibility.objects.create(donor_group=self.bg_o_neg, recipient_group=self.bg_o_neg)
        BloodCompatibility.objects.create(donor_group=self.bg_o_neg, recipient_group=self.bg_o_pos)
        BloodCompatibility.objects.create(donor_group=self.bg_o_pos, recipient_group=self.bg_o_pos)

        # Donor 1: O- who never donated (Eligible)
        self.user1 = User.objects.create_user(username='d1', phone_number='+8801711111111', role=User.Role.DONOR)
        self.donor1 = DonorProfile.objects.create(
            user=self.user1, blood_group=self.bg_o_neg, gender='M',
            date_of_birth=date(1990, 1, 1), district=self.district,
            full_address='Mirpur', is_available=True, last_donation_date=None
        )

        # Donor 2: O+ who donated 30 days ago (Ineligible, needs 120 days)
        self.user2 = User.objects.create_user(username='d2', phone_number='+8801722222222', role=User.Role.DONOR)
        self.donor2 = DonorProfile.objects.create(
            user=self.user2, blood_group=self.bg_o_pos, gender='M',
            date_of_birth=date(1992, 1, 1), district=self.district,
            full_address='Gulshan', is_available=True, last_donation_date=date.today() - timedelta(days=30)
        )

    def test_donation_eligibility_120_days_rule(self):
        # Donor 1 never donated: must be eligible
        self.assertTrue(self.donor1.is_eligible)
        self.assertEqual(self.donor1.days_remaining, 0)

        # Donor 2 donated 30 days ago: must be ineligible
        self.assertFalse(self.donor2.is_eligible)
        self.assertEqual(self.donor2.days_remaining, 90)

    def test_donor_availability_toggle(self):
        self.client.force_login(self.user1)
        resp = self.client.post(reverse('donors:toggle_availability'))
        self.assertEqual(resp.status_code, 302)
        self.donor1.refresh_from_db()
        self.assertFalse(self.donor1.is_available)

    def test_intelligent_abo_compatibility_search(self):
        """Searching for O+ recipient should find O- donor due to ABO red cell compatibility!"""
        resp = self.client.get(reverse('donors:search'), {
            'blood_group': self.bg_o_pos.id,
            'eligible_only': '1'
        })
        self.assertEqual(resp.status_code, 200)
        donors = resp.context['donors']
        donor_ids = [d.id for d in donors]
        # Donor 1 (O-) is compatible and eligible: must be in search results!
        self.assertIn(self.donor1.id, donor_ids)
        # Donor 2 (O+) is ineligible (<120 days): must NOT be in eligible search results
        self.assertNotIn(self.donor2.id, donor_ids)
