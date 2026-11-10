from django.db import models
from django.conf import settings


class Notification(models.Model):
    """
    In-app alerts and notifications delivered to users across the platform.
    """
    class Type(models.TextChoices):
        REQUEST = 'REQUEST', 'Blood Request Update'
        DONOR_MATCH = 'DONOR_MATCH', 'Matching Donor Found'
        DONATION = 'DONATION', 'Donation Completed'
        SYSTEM = 'SYSTEM', 'System Alert'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        db_index=True
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=30,
        choices=Type.choices,
        default=Type.SYSTEM,
        db_index=True
    )
    is_read = models.BooleanField(default=False, db_index=True)
    link = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f"[{self.get_notification_type_display()}] {self.title} -> {self.user.username}"

    @classmethod
    def send(cls, user, title, message, notification_type=Type.SYSTEM, link=""):
        """Convenience factory method to generate in-app notification."""
        return cls.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link
        )
