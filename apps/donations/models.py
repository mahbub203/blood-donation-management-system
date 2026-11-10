from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
import random
import string
from core.models import BloodGroup
from donors.models import DonorProfile
from blood_requests.models import BloodRequest
from hospitals.models import HospitalOrganization


def generate_donation_code():
    date_str = timezone.now().strftime('%Y%m%d')
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"DON-{date_str}-{suffix}"


class Donation(models.Model):
    """
    Formal record of an individual blood donation event.
    Only authorized Administrators or Verified Hospital Accounts can certify 'COMPLETED' status.
    """
    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        REJECTED = 'REJECTED', 'Rejected'

    donation_code = models.CharField(
        max_length=24,
        unique=True,
        default=generate_donation_code,
        editable=False,
        db_index=True
    )
    donor = models.ForeignKey(
        DonorProfile,
        on_delete=models.CASCADE,
        related_name='donations',
        db_index=True
    )
    blood_request = models.ForeignKey(
        BloodRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='donations'
    )
    donation_date = models.DateField(db_index=True)
    donation_location = models.CharField(max_length=255, help_text="Hospital name, Clinic, or Blood Donation Camp")
    blood_group = models.ForeignKey(
        BloodGroup,
        on_delete=models.PROTECT,
        related_name='donations'
    )
    units_donated = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Standard whole blood units (typically 450ml)"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
        db_index=True
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_donations'
    )
    remarks = models.TextField(blank=True, help_text="Clinical observations, bag serial numbers, or post-donation notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-donation_date', '-created_at']
        indexes = [
            models.Index(fields=['donor', 'donation_date'], name='idx_don_donor_date'),
            models.Index(fields=['status', 'donation_date'], name='idx_don_status_date'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(units_donated__gt=0),
                name='chk_donation_units_positive'
            ),
            # Concurrency & integrity: prevent duplicate completed donation for same donor on same day
            models.UniqueConstraint(
                fields=['donor', 'donation_date'],
                condition=models.Q(status='COMPLETED'),
                name='unique_completed_donation_per_day'
            )
        ]
        verbose_name = 'Donation'
        verbose_name_plural = 'Donations'

    def __str__(self):
        return f"[{self.donation_code}] {self.donor.user.get_full_name()} - {self.donation_date} ({self.get_status_display()})"

    @property
    def status_badge_class(self):
        mapping = {
            self.Status.SCHEDULED: 'badge bg-warning text-dark',
            self.Status.COMPLETED: 'badge bg-success',
            self.Status.CANCELLED: 'badge bg-secondary',
            self.Status.REJECTED: 'badge bg-danger',
        }
        return mapping.get(self.status, 'badge bg-secondary')


class DonationAppointment(models.Model):
    """
    Coordination appointment connecting an eligible donor to a specific blood request at a hospital.
    """
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('CONFIRMED', 'Confirmed by Donor'),
        ('ATTENDED', 'Attended / Donated'),
        ('CANCELLED', 'Cancelled'),
    ]

    donor = models.ForeignKey(
        DonorProfile,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    blood_request = models.ForeignKey(
        BloodRequest,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    hospital_org = models.ForeignKey(
        HospitalOrganization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments'
    )
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['appointment_date', 'appointment_time']
        verbose_name = 'Donation Appointment'
        verbose_name_plural = 'Donation Appointments'

    def __str__(self):
        return f"Appointment: {self.donor.user.get_full_name()} for {self.blood_request.patient_name} on {self.appointment_date}"
