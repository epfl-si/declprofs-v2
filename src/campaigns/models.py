from django.db import models
from django.utils import timezone


class Campaign(models.Model):
    year = models.PositiveIntegerField(unique=True)
    opening_date = models.DateTimeField()
    closing_date = models.DateTimeField()
    was_opened = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Campaign"
        verbose_name_plural = "Campaigns"
        ordering = ["-year"]

    def __str__(self):
        return f"Campaign {self.year}"

    @property
    def is_open(self):
        today = timezone.now()
        return self.opening_date <= today <= self.closing_date
