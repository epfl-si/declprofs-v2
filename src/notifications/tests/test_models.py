from django.test import TestCase
from django.conf import settings

from notifications.models import Notification


class NotificationModelTest(TestCase):

    def test_notification_str(self):

        notification = Notification.objects.create(
            name=Notification.NotificationType.REMINDER,
            subject="Reminder",
            body="Body",
        )

        self.assertEqual(
            str(notification),
            "Reminder",
        )

    def test_parse_addresses(self):

        addresses = """
        user1@example.com
        user2@example.com, user3@example.com
        """

        result = Notification.parse_addresses(
            addresses
        )

        self.assertEqual(
            result,
            [
                "user1@example.com",
                "user2@example.com",
                "user3@example.com",
            ],
        )

    def test_parse_empty_addresses(self):

        self.assertEqual(
            Notification.parse_addresses(""),
            [],
        )

        self.assertEqual(
            Notification.parse_addresses(None),
            [],
        )

    def test_get_recipients_in_test_mode(self):

        settings.ENV_MODE = "test"

        notification = Notification.objects.create(
            name=Notification.NotificationType.REMINDER,
            subject="Reminder",
            body="Body",
            test_to="""
                test1@example.com
                test2@example.com
            """,
            test_cc="cc@example.com",
            test_bcc="bcc@example.com",
        )

        recipients = notification.get_recipients(
            {
                "to": "ignored@example.com",
            }
        )

        self.assertEqual(
            recipients["to"],
            [
                "test1@example.com",
                "test2@example.com",
            ],
        )

        self.assertEqual(
            recipients["cc"],
            [
                "cc@example.com",
            ],
        )

        self.assertEqual(
            recipients["bcc"],
            [
                "bcc@example.com",
            ],
        )

    def test_get_recipients_in_prod_mode(self):

        settings.ENV_MODE = "prod"

        notification = Notification.objects.create(
            name=Notification.NotificationType.SUBMISSION,
            subject="Submission",
            body="Body",
        )

        recipients = notification.get_recipients(
            {
                "to": "user@example.com,user2@example.com",
                "cc": "cc@example.com",
                "bcc": "",
            }
        )

        self.assertEqual(
            recipients["to"],
            [
                "user@example.com",
                "user2@example.com",
            ],
        )

        self.assertEqual(
            recipients["cc"],
            [
                "cc@example.com",
            ],
        )

        self.assertEqual(
            recipients["bcc"],
            [],
        )