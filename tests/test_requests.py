from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from core.models import District, BloodGroup, BloodCompatibility
from blood_requests.models import BloodRequest
from donors.models import DonorProfile

User = get_user_model()


class BloodRequestTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.district = District.objects.create(name='Dhaka', division='Dhaka')
        self.bg_b_pos = BloodGroup.objects.create(name='B+')
        self.user = User.objects.create_user(
            username='req_tester',
            phone_number='+8801733333333',
            role=User.Role.REQUESTER
        )

    def test_create_blood_request(self):
        self.client.force_login(self.user)
        resp = self.client.post(reverse('blood_requests:create'), {
            'patient_name': 'Test Patient',
            'blood_group': self.bg_b_pos.id,
            'units_needed': 2,
            'hospital_name': 'DMCH',
            'hospital_address': 'Ward 5, DMCH',
            'district': self.district.id,
            'required_date': (date.today() + timedelta(days=2)).strftime('%Y-%m-%d'),
            'emergency_level': 'CRITICAL',
            'contact_number': '+8801733333333',
            'description': 'Urgent surgery requirements',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(BloodRequest.objects.count(), 1)
        req = BloodRequest.objects.first()
        self.assertEqual(req.patient_name, 'Test Patient')
        self.assertEqual(req.units_needed, 2)
        self.assertTrue(req.request_code.startswith('REQ-'))

    def test_cancel_blood_request(self):
        req = BloodRequest.objects.create(
            requester=self.user,
            patient_name='Cancel Patient',
            blood_group=self.bg_b_pos,
            units_needed=1,
            hospital_name='BSMMU',
            hospital_address='Shahbag',
            district=self.district,
            required_date=date.today() + timedelta(days=1),
            emergency_level='NORMAL',
            contact_number='+8801733333333',
            description='Test cancellation'
        )
        self.client.force_login(self.user)
        resp = self.client.get(reverse('blood_requests:cancel', kwargs={'request_id': req.id}))
        self.assertEqual(resp.status_code, 302)
        req.refresh_from_db()
        self.assertEqual(req.status, BloodRequest.Status.CANCELLED)
