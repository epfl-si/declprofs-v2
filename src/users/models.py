from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    sciper = models.CharField(max_length=10, unique=True)
    unit = models.CharField(max_length=255, blank=True)

    has_access = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.sciper})"


class UserYear(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="years")
    year = models.PositiveIntegerField()

    # Administrative decision
    is_eligible = models.BooleanField(default=False)
    is_exempted = models.BooleanField(default=False)
    is_employed = models.BooleanField(default=True)

    # User's latest business activity
    updated_at = models.DateTimeField(null=True, blank=True)
    reminder_at = models.DateTimeField(null=True, blank=True)

    # Activity statistics
    draft_count = models.PositiveIntegerField(default=0)
    missing_count = models.PositiveIntegerField(default=1)
    submitted_count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "year"],
                name="unique_user_year",
            )
        ]

    @property
    def is_complete(self):
        return (
            self.submitted_count > 0
            and self.draft_count == 0
            and self.missing_count == 0
        )

    def add_draft_activity(self, save=True):
        # A new activity is always a draft
        self.draft_count += 1
        self.missing_count = 0

        if save:
            self.save()

    def add_submitted_activity(self, save=True):
        # When importing from script
        self.submitted_count += 1
        self.missing_count = 0

        if save:
            self.save()

    def promote_activity(self, save=True):
        # Promote a draft to submitted activity
        self.draft_count -= 1
        self.submitted_count += 1

        if save:
            self.save()

    def remove_activity(self, activity, save=True):
        if activity.is_draft:
            self.draft_count -= 1
        elif activity.is_submitted:
            self.submitted_count -= 1
        if self.draft_count == 0 and self.submitted_count == 0:
            self.missing_count = 1
 
        if save:
            self.save()
