from django.conf import settings
from django.db import models


class Notification(models.Model):

    class NotificationType(models.TextChoices):
        REMINDER = "reminder", "Reminder"
        SUBMISSION = "submission", "Submission"
        APR_MODIFICATION = "apr_modification", "APR modification"

    name = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        unique=True,
    )

    subject = models.CharField(max_length=255)
    body = models.TextField()

    test_to = models.TextField(
        blank=True,
        help_text="One email address per line or separated by commas"
    )
    prod_to = models.TextField(
        blank=True,
        help_text="One email address per line or separated by commas"
    )
    test_cc = models.TextField(
        blank=True,
        help_text="One email address per line or separated by commas"
    )
    prod_cc = models.TextField(
        blank=True,
        help_text="One email address per line or separated by commas"
    )
    test_bcc = models.TextField(
        blank=True,
        help_text="One email address per line or separated by commas"
    )
    prod_bcc = models.TextField(
        blank=True,
        help_text="One email address per line or separated by commas"
    )

    class Meta:
        verbose_name = "Email template"
        verbose_name_plural = "Email templates"

    def __str__(self):
        #return self.name
        return self.get_name_display()

    @staticmethod
    def parse_addresses(addresses):
        """Return an e-mails list"""
        if not addresses:
            return []
        return [
            addr.strip()
            for addr in addresses.replace("\n", ",").split(",")
            if addr.strip()
        ]

    def get_recipients(self, context):
        if settings.ENV_MODE == "prod":
            return {
                "to": self.parse_addresses(self.prod_to.strip() or context.get("to")),
                "cc": self.parse_addresses(self.prod_cc.strip() or context.get("cc")),
                "bcc": self.parse_addresses(self.prod_bcc.strip() or context.get("bcc")),
            }

        return {
            "to": self.parse_addresses(self.test_to.strip()),
            "cc": self.parse_addresses(self.test_cc.strip()),
            "bcc": self.parse_addresses(self.test_bcc.strip()),
        }
