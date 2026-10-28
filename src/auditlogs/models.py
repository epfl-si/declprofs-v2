from django.conf import settings
from django.db import models

from activities.models import Activity


class ActivityLog(models.Model):

    class Action(models.TextChoices):
        CREATED = "created", "Created"
        DUPLICATED = "duplicated", "Duplicated"
        UPDATED = "updated", "Updated"
        SUBMITTED = "submitted", "Submitted"
        DELETED = "deleted", "Deleted"

    activity = models.ForeignKey(
        Activity,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs",
    )

    action = models.CharField(
        max_length=30,
        choices=Action.choices,
    )

    changes = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class EmailLog(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    notification_type = models.CharField(max_length=100)

    subject = models.CharField(max_length=255)

    recipients = models.JSONField(default=dict)

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )

    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.notification_type} - {self.status}"