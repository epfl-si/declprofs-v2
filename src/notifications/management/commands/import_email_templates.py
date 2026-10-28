from django.core.management.base import BaseCommand
from notifications.models import Notification


EMAIL_TEMPLATES = [
    {
        "name": Notification.NotificationType.REMINDER,
        "subject": "REMINDER- Outside activities disclosure",
        "test_to": "lindo.duratti@epfl.ch",
        "test_bcc": "lindo.duratti@epfl.ch, durlindo@gmail.com",
        "body": """
<p>Dear Professors,</p>

<p>This is a kind reminder to report your outside activities and finalize the disclosure for {{year}} on the EPFL platform (https://declprofs.epfl.ch/). According to LEX 4.1.1, activities should be disclosed prior to starting them or if any changes in their nature or in your involvement occur.</p>

<p>Please note that, once the disclosure is complete, it is necessary that you officially submit it via the Validate button.</p>

<p>Even if you have no activity to disclose, please fill out one line in the online form indicating "N/A", and submit your disclosure.</p>

<p>We thank you for your cooperation and are available should you have any questions.</p>

<p>Kind regards,</p>

<p>Faculty Affairs Team</p>
""",
    },
    {
        "name": Notification.NotificationType.SUBMISSION,
        "subject": "Prof. {{name}} annual disclosure of outside activities = ok",
        "test_to": "lindo.duratti@epfl.ch",
        "test_cc": "lindo.duratti@epfl.ch, durlindo@gmail.com",
        "body": """
<p>Dear Professor {{name}},</p>

<p>The disclosure of your outside activities, as of {{date}}, has been updated successfully.</p>

<p>Thank you and best regards,</p>

<p>EPFL Faculty Affairs Team</p>
""",
    },
    {
        "name": Notification.NotificationType.APR_MODIFICATION,
        "subject": "APR modification - annual disclosure of {{year}} outside activities",
        "test_to": "lindo.duratti@epfl.ch",
        "test_cc": "lindo.duratti@epfl.ch, durlindo@gmail.com",
        "body": """
<p>Dear Professor {{name}},</p>

<p>Your disclosure of {{year}} outside activities has been modified/updated by Faculty Affairs staff.</p>

<p>You may check it on https://declprofs.epfl.ch/</p>

<p>Thank you and best regards,</p>

<p>EPFL Faculty Affairs Team</p>
""",
    },
]


class Command(BaseCommand):
    help = "Import email notification templates"

    def handle(self, *args, **options):
        for template in EMAIL_TEMPLATES:
            notification, created = Notification.objects.update_or_create(
                name=template["name"],
                defaults={
                    "subject": template["subject"],
                    "body": template["body"].strip(),
                    "test_to": template.get("test_to", ""),
                    "test_cc": template.get("test_cc", ""),
                    "test_bcc": template.get("test_bcc", ""),
                },
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created template: {notification.name}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Updated template: {notification.name}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Email templates import completed."
            )
        )
