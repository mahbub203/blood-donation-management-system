from django.db import models
from django.conf import settings
from core.models import District, Upazila


class HospitalOrganization(models.Model):
    """
    Healthcare facilities, Blood Banks, and Humanitarian NGOs coordinating donations in Bangladesh.
    Must be verified by System Administrators before accessing privileged actions.
    """
    class OrgType(models.TextChoices):
        HOSPITAL = 'HOSPITAL', 'Hospital'
        CLINIC = 'CLINIC', 'Specialized Clinic'
        BLOOD_BANK = 'BLOOD_BANK', 'Blood Bank / Transfusion Center'
        NGO = 'NGO', 'Humanitarian NGO'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hospital_profile'
    )
    org_name = models.CharField(max_length=255, db_index=True)
    org_type = models.CharField(
        max_length=30,
        choices=OrgType.choices,
        default=OrgType.HOSPITAL,
        db_index=True
    )
    license_number = models.CharField(
        max_length=100,
        unique=True,
        help_text="DGHS (Directorate General of Health Services) registration or Govt license number"
    )
    district = models.ForeignKey(
        District,
        on_delete=models.PROTECT,
        related_name='hospitals'
    )
    upazila = models.ForeignKey(
        Upazila,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hospitals'
    )
    address = models.TextField()
    contact_person = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    is_verified = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Approved by System Administrator to initiate and certify donations"
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_organizations'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['org_name']
        verbose_name = 'Hospital / Organization'
        verbose_name_plural = 'Hospitals & Organizations'

    def __str__(self):
        status = "Verified" if self.is_verified else "Pending Verification"
        return f"{self.org_name} [{self.get_org_type_display()}] - {status}"
