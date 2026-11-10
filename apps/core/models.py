from django.db import models


class District(models.Model):
    """
    Districts of Bangladesh (64 districts across 8 divisions).
    """
    DIVISION_CHOICES = [
        ('Dhaka', 'Dhaka'),
        ('Chittagong', 'Chittagong'),
        ('Rajshahi', 'Rajshahi'),
        ('Khulna', 'Khulna'),
        ('Barisal', 'Barisal'),
        ('Sylhet', 'Sylhet'),
        ('Rangpur', 'Rangpur'),
        ('Mymensingh', 'Mymensingh'),
    ]

    name = models.CharField(max_length=100, unique=True, db_index=True)
    division = models.CharField(max_length=50, choices=DIVISION_CHOICES, db_index=True)
    bn_name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['division', 'name']
        verbose_name = 'District'
        verbose_name_plural = 'Districts'

    def __str__(self):
        return f"{self.name} ({self.division})"


class Upazila(models.Model):
    """
    Upazilas/Sub-districts of Bangladesh within a District.
    """
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='upazilas')
    name = models.CharField(max_length=100)
    bn_name = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['district', 'name']
        constraints = [
            models.UniqueConstraint(fields=['district', 'name'], name='unique_district_upazila')
        ]
        verbose_name = 'Upazila'
        verbose_name_plural = 'Upazilas'

    def __str__(self):
        return f"{self.name}, {self.district.name}"


class BloodGroup(models.Model):
    """
    Standard ABO and Rh Blood Groups.
    """
    name = models.CharField(max_length=5, unique=True, db_index=True)
    antigen = models.CharField(max_length=20, blank=True)
    antibody = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Blood Group'
        verbose_name_plural = 'Blood Groups'

    def __str__(self):
        return self.name

    def compatible_donors(self):
        """Returns blood groups that can donate red cells to this blood group."""
        return BloodGroup.objects.filter(can_donate_to__recipient_group=self)

    def compatible_recipients(self):
        """Returns blood groups that can receive red cells from this blood group."""
        return BloodGroup.objects.filter(can_receive_from__donor_group=self)


class BloodCompatibility(models.Model):
    """
    Normalized red-cell transfusion compatibility matrix.
    Universal donor: O-
    Universal recipient: AB+
    """
    donor_group = models.ForeignKey(BloodGroup, on_delete=models.CASCADE, related_name='can_donate_to')
    recipient_group = models.ForeignKey(BloodGroup, on_delete=models.CASCADE, related_name='can_receive_from')
    notes = models.CharField(max_length=255, blank=True, default="Red blood cell compatible")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['donor_group', 'recipient_group'], name='unique_compatibility_pair')
        ]
        verbose_name = 'Blood Compatibility'
        verbose_name_plural = 'Blood Compatibilities'

    def __str__(self):
        return f"{self.donor_group.name} -> {self.recipient_group.name}"
