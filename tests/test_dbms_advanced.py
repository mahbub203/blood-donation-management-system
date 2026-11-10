from django.test import TestCase
from django.db import connection, IntegrityError
from datetime import date
from core.models import District, BloodGroup
from blood_requests.models import BloodRequest
from accounts.models import User


class AdvancedDBMSConstraintsTests(TestCase):
    def setUp(self):
        self.district = District.objects.create(name='Dhaka', division='Dhaka')
        self.bg = BloodGroup.objects.create(name='AB+')
        self.user = User.objects.create_user(
            username='constraint_user',
            phone_number='+8801755555555',
            role=User.Role.REQUESTER
        )

    def test_chk_blood_request_units_needed_positive_constraint(self):
        """Database Check Constraint should reject units_needed <= 0."""
        with self.assertRaises(IntegrityError):
            BloodRequest.objects.create(
                requester=self.user,
                patient_name='Invalid Units Patient',
                blood_group=self.bg,
                units_needed=0,  # Invalid! Fails chk_blood_request_units_needed_positive
                hospital_name='Hospital',
                hospital_address='Address',
                district=self.district,
                required_date=date.today(),
                emergency_level='NORMAL',
                contact_number='+8801755555555',
                description='Testing check constraint'
            )

    def test_postgresql_view_execution(self):
        """Verify PostgreSQL views execute and return proper columns."""
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM view_available_eligible_donors LIMIT 1;")
            desc = [col[0] for col in cursor.description]
            self.assertIn('donor_profile_id', desc)
            self.assertIn('is_eligible', desc)
            self.assertIn('days_remaining', desc)
