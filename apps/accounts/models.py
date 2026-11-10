from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator


phone_regex = RegexValidator(
    regex=r'^(?:\+88|88)?(01[3-9]\d{8})$',
    message="Phone number must be entered in Bangladesh format: '+8801XXXXXXXXX' or '01XXXXXXXXX'."
)


class User(AbstractUser):
    """
    Custom User Model supporting 4 distinct roles:
    1. Administrator
    2. Blood Donor
    3. Blood Requester
    4. Hospital / Healthcare Organization
    """
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Administrator')
        DONOR = 'DONOR', _('Blood Donor')
        REQUESTER = 'REQUESTER', _('Blood Requester')
        HOSPITAL = 'HOSPITAL', _('Hospital / Organization')

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.DONOR,
        db_index=True,
        help_text=_("Designates the user's operational role within LifeDrop BD.")
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=20,
        unique=True,
        db_index=True,
        help_text=_("Primary contact number in Bangladesh (+880 format)")
    )
    is_verified = models.BooleanField(
        default=False,
        help_text=_("Designates whether the user or organization has been verified.")
    )
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_joined']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        full_name = self.get_full_name()
        display = full_name if full_name else self.username
        return f"{display} ({self.get_role_display()})"

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_donor_role(self):
        return self.role == self.Role.DONOR

    @property
    def is_requester_role(self):
        return self.role == self.Role.REQUESTER

    @property
    def is_hospital_role(self):
        return self.role == self.Role.HOSPITAL

    @property
    def display_phone(self):
        """Standardizes phone display format."""
        num = self.phone_number
        if num.startswith('+880'):
            return f"+880 {num[4:8]}-{num[8:]}"
        elif num.startswith('01'):
            return f"+880 {num[1:5]}-{num[5:]}"
        return num
