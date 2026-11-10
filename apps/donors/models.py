from django.db import models
from django.conf import settings
from datetime import date, timedelta
from core.models import District, Upazila, BloodGroup


class DonorProfile(models.Model):
    """
    Detailed profile for Blood Donors.
    Implements configurable 120-day donation interval rule (conservative academic baseline).
    """
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='donor_profile'
    )
    blood_group = models.ForeignKey(
        BloodGroup,
        on_delete=models.PROTECT,
        related_name='donors',
        db_index=True
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField(help_text="Donors must typically be at least 18 years of age.")
    district = models.ForeignKey(
        District,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='donors',
        db_index=True
    )
    upazila = models.ForeignKey(
        Upazila,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='donors'
    )
    full_address = models.TextField(help_text="Street, House/Road, Village or Area")
    last_donation_date = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Date of most recent completed blood donation."
    )
    is_available = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Current willingness to be contacted for blood donation."
    )
    emergency_contact = models.CharField(
        max_length=20,
        blank=True,
        help_text="Secondary contact number if primary is unreachable"
    )
    bio = models.TextField(blank=True, help_text="Short donor note or motivation")
    total_donations = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['district', 'is_available'], name='idx_donor_district_avail'),
            models.Index(fields=['blood_group', 'is_available'], name='idx_donor_blood_avail'),
            models.Index(fields=['last_donation_date'], name='idx_donor_last_donation'),
        ]
        verbose_name = 'Donor Profile'
        verbose_name_plural = 'Donor Profiles'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} [{self.blood_group.name}]"

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def days_since_last_donation(self):
        if not self.last_donation_date:
            return None
        return (date.today() - self.last_donation_date).days

    @property
    def is_eligible(self):
        """
        Calculates preliminary eligibility based on configured interval (default 120 days).
        Actual medical fitness must always be verified by medical personnel.
        """
        if not self.is_available:
            return False
        if not self.last_donation_date:
            return True
        interval = getattr(settings, 'DEFAULT_DONATION_INTERVAL_DAYS', 120)
        return self.days_since_last_donation >= interval

    @property
    def next_eligible_date(self):
        if not self.last_donation_date:
            return date.today()
        interval = getattr(settings, 'DEFAULT_DONATION_INTERVAL_DAYS', 120)
        return self.last_donation_date + timedelta(days=interval)

    @property
    def days_remaining(self):
        """Days remaining until donor becomes eligible again."""
        if not self.last_donation_date:
            return 0
        interval = getattr(settings, 'DEFAULT_DONATION_INTERVAL_DAYS', 120)
        diff = interval - self.days_since_last_donation
        return max(0, diff)

    @property
    def masked_phone(self):
        """Protects donor privacy in public listings: e.g. +880 1712-***89"""
        phone = self.user.phone_number
        if len(phone) >= 10:
            return phone[:7] + '***' + phone[-2:]
        return 'Protected'
