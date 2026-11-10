from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import District, Upazila, BloodGroup
from donors.models import DonorProfile
from datetime import date

User = get_user_model()


class AuthenticationAndRBACTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.district = District.objects.create(name='Dhaka', division='Dhaka')
        self.upazila = Upazila.objects.create(district=self.district, name='Dhanmondi')
        self.blood_group = BloodGroup.objects.create(name='O+')

        # Create Admin
        self.admin = User.objects.create_superuser(
            username='test_admin',
            email='admin@test.com',
            password='Password@123',
            phone_number='+8801700000001',
            role=User.Role.ADMIN
        )

        # Create Donor
        self.donor_user = User.objects.create_user(
            username='test_donor',
            email='donor@test.com',
            password='Password@123',
            phone_number='+8801700000002',
            role=User.Role.DONOR
        )
        self.donor_profile = DonorProfile.objects.create(
            user=self.donor_user,
            blood_group=self.blood_group,
            gender='M',
            date_of_birth=date(1995, 1, 1),
            district=self.district,
            upazila=self.upazila,
            full_address='Dhanmondi, Dhaka',
            is_available=True
        )

        # Create Requester
        self.requester_user = User.objects.create_user(
            username='test_requester',
            email='requester@test.com',
            password='Password@123',
            phone_number='+8801700000003',
            role=User.Role.REQUESTER
        )

    def test_user_login_success(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'test_donor',
            'password': 'Password@123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:dashboard_redirect'), target_status_code=302)

    def test_role_based_dashboard_redirects(self):
        # Test Donor redirect
        self.client.login(username='test_donor', password='Password@123')
        resp = self.client.get(reverse('accounts:dashboard_redirect'))
        self.assertRedirects(resp, reverse('donors:dashboard'))
        self.client.logout()

        # Test Requester redirect
        self.client.login(username='test_requester', password='Password@123')
        resp = self.client.get(reverse('accounts:dashboard_redirect'))
        self.assertRedirects(resp, reverse('blood_requests:my_requests'))
        self.client.logout()

        # Test Admin redirect
        self.client.login(username='test_admin', password='Password@123')
        resp = self.client.get(reverse('accounts:dashboard_redirect'))
        self.assertRedirects(resp, reverse('analytics:admin_dashboard'))

    def test_unauthorized_admin_access_restricted(self):
        """Donors must not be able to access the admin dashboard."""
        self.client.login(username='test_donor', password='Password@123')
        resp = self.client.get(reverse('analytics:admin_dashboard'))
        self.assertEqual(resp.status_code, 302)  # Redirects away because of user_passes_test
