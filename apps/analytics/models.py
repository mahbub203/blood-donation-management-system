from django.db import models
from django.conf import settings


class ActivityLog(models.Model):
    """
    Centralized system audit log for critical database events:
    - User authentications
    - Blood request submissions and status modifications
    - Certified donation transactions
    - Administrator overrides and organization verifications
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs'
    )
    action = models.CharField(max_length=150, db_index=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'

    def __str__(self):
        actor = self.user.username if self.user else "System"
        return f"[{self.created_at.strftime('%Y-%m-%d %H:%M')}] {actor}: {self.action}"

    @classmethod
    def log(cls, action, user=None, details="", ip_address=None):
        return cls.objects.create(
            user=user,
            action=action,
            details=details,
            ip_address=ip_address
        )
