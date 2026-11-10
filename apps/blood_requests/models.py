from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
import random
import string
from core.models import District, Upazila, BloodGroup


def generate_request_code():
    """Generates unique friendly reference: REQ-YYYYMMDD-XXXX"""
    date_str = timezone.now().strftime('%Y%m%d')
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"REQ-{date_str}-{suffix}"


class RequesterProfile(models.Model):
    """
    Profile extension for Blood Requesters (patients, relatives, or community representatives).
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='requester_profile'
    )
    district = models.ForeignKey(
        District,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requesters'
    )
    upazila = models.ForeignKey(
        Upazila,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requesters'
    )
    alternate_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Requester Profile'
        verbose_name_plural = 'Requester Profiles'

    def __str__(self):
        return f"Requester: {self.user.get_full_name() or self.user.username}"


class BloodRequest(models.Model):
    """
    Blood Donation Requests created by patients, family members, or authorized hospitals.
    """
    class EmergencyLevel(models.TextChoices):
        NORMAL = 'NORMAL', 'Normal'
        URGENT = 'URGENT', 'Urgent'
        CRITICAL = 'CRITICAL', 'Critical'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        DONOR_FOUND = 'DONOR_FOUND', 'Donor Found'
        FULFILLED = 'FULFILLED', 'Fulfilled'
        REJECTED = 'REJECTED', 'Rejected'
        CANCELLED = 'CANCELLED', 'Cancelled'

    request_code = models.CharField(
        max_length=24,
        unique=True,
        default=generate_request_code,
        editable=False,
        db_index=True
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blood_requests'
    )
    patient_name = models.CharField(max_length=150)
    blood_group = models.ForeignKey(
        BloodGroup,
        on_delete=models.PROTECT,
        related_name='blood_requests',
        db_index=True
    )
    units_needed = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Number of 450ml blood bags/units required"
    )
    hospital_name = models.CharField(max_length=200)
    hospital_address = models.TextField()
    district = models.ForeignKey(
        District,
        on_delete=models.PROTECT,
        related_name='blood_requests',
        db_index=True
    )
    upazila = models.ForeignKey(
        Upazila,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blood_requests'
    )
    required_date = models.DateField(db_index=True)
    required_time = models.TimeField(null=True, blank=True)
    emergency_level = models.CharField(
        max_length=20,
        choices=EmergencyLevel.choices,
        default=EmergencyLevel.NORMAL,
        db_index=True
    )
    contact_number = models.CharField(max_length=20)
    description = models.TextField(help_text="Clinical reason, patient ward/bed, hemoglobin count, etc.")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    admin_notes = models.TextField(blank=True, help_text="Internal notes or verification remarks")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-required_date', '-created_at']
        indexes = [
            models.Index(fields=['district', 'status'], name='idx_req_district_status'),
            models.Index(fields=['blood_group', 'status'], name='idx_req_blood_status'),
            models.Index(fields=['emergency_level', 'status'], name='idx_req_urgency_status'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(units_needed__gt=0),
                name='chk_blood_request_units_needed_positive'
            )
        ]
        verbose_name = 'Blood Request'
        verbose_name_plural = 'Blood Requests'

    def __str__(self):
        return f"[{self.request_code}] {self.blood_group.name} for {self.patient_name} ({self.get_status_display()})"

    @property
    def urgency_badge_class(self):
        mapping = {
            self.EmergencyLevel.CRITICAL: 'badge bg-danger animate-pulse',
            self.EmergencyLevel.URGENT: 'badge bg-warning text-dark',
            self.EmergencyLevel.NORMAL: 'badge bg-info text-dark',
        }
        return mapping.get(self.emergency_level, 'badge bg-secondary')

    @property
    def status_badge_class(self):
        mapping = {
            self.Status.PENDING: 'badge bg-warning text-dark',
            self.Status.APPROVED: 'badge bg-primary',
            self.Status.DONOR_FOUND: 'badge bg-info text-dark',
            self.Status.FULFILLED: 'badge bg-success',
            self.Status.REJECTED: 'badge bg-danger',
            self.Status.CANCELLED: 'badge bg-secondary',
        }
        return mapping.get(self.status, 'badge bg-secondary')
