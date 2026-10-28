from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Activity(models.Model):

    class ActivityStatusType(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"

    status = models.CharField(
        max_length=20,
        choices=ActivityStatusType.choices,
        default=ActivityStatusType.DRAFT,
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activities")
    activity = models.TextField()
    principal = models.TextField()
    comments = models.TextField(blank=True)
    comments_apr = models.TextField(blank=True)
    date_start = models.DateField()
    date_end = models.DateField(null=True, blank=True)

    class Meta:
        ordering = [
            "-date_start",
            "-id",
        ]

    def clean(self):
        super().clean()

        if not self.date_start:
            raise ValidationError(
                {
                    "date_start": ""
                }
            )

        if self.date_end is not None and self.date_end < self.date_start:
            raise ValidationError(
                {
                    "date_end": "End date must be greater or equal than start date."
                }
            )

    def __str__(self):
        return f"{self.activity} - {self.principal}"

    @property
    def is_draft(self):
        return self.status == self.ActivityStatusType.DRAFT

    @property
    def is_submitted(self):
        return self.status == self.ActivityStatusType.SUBMITTED
    
    def set_draft(self, save=True):
        self.status = self.ActivityStatusType.DRAFT
        if save:
            self.save(update_fields=["status"])

    def set_submitted(self, save=True):
        self.status = self.ActivityStatusType.SUBMITTED
        if save:
            self.save(update_fields=["status"])

    def get_years(self):
            start_year = self.date_start.year

            end_year = (
                self.date_end.year
                if self.date_end
                else max(start_year, timezone.now().year)
            )

            return set(range(start_year, end_year + 1))

    def to_log_dict(self):
        return {
            "status": self.status,
            "user": str(self.user),
            "activity": self.activity,
            "principal": self.principal,
            "comments": self.comments,
            "comments_apr": self.comments_apr,
            "date_start": (
                self.date_start.isoformat()
                if self.date_start
                else None
            ),
            "date_end": (
                self.date_end.isoformat()
                if self.date_end
                else None
            ),
        }

    def get_changes(self, old_values):
        new_values = self.to_log_dict()

        changes = {
            field: {
                "old": old_values[field],
                "new": new_values[field],
            }
            for field in new_values
            if old_values.get(field) != new_values[field]
        }

        changes["user"] = str(self.user) if self.user else None

        return changes
