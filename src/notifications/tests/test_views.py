from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch

from campaigns.models import Campaign
from notifications.models import Notification
from users.models import UserYear


User = get_user_model()


class NotificationViewTest(TestCase):

    def setUp(self):

        self.admin = User.objects.create_superuser(
            username="admin",
            password="password",
            sciper="999999",
        )

        self.user1 = User.objects.create_user(
            username="prof1",
            password="password",
            sciper="111111",
            first_name="Alice",
            last_name="Smith",
            email="alice@example.com",
        )

        self.user2 = User.objects.create_user(
            username="prof2",
            password="password",
            sciper="222222",
            first_name="Bob",
            last_name="Jones",
            email="",
        )

        self.campaign = Campaign.objects.create(
            year=2026,
            opening_date=timezone.now() - timedelta(days=1),
            closing_date=timezone.now() + timedelta(days=10),
        )

        self.user_year1 = UserYear.objects.create(
            user=self.user1,
            year=2026,
            is_eligible=True,
        )

        self.user_year2 = UserYear.objects.create(
            user=self.user2,
            year=2026,
            is_eligible=True,
        )

    def test_admin_can_access_notifications_page(self):

        self.client.force_login(
            self.admin,
        )

        response = self.client.get(
            reverse("notifications"),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertIn(
            "formset",
            response.context,
        )

    def test_user_cannot_access_notifications_page(self):

        self.client.force_login(
            self.user1,
        )

        response = self.client.get(
            reverse("notifications"),
        )

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_admin_can_save_notification_templates(self):

        notification = Notification.objects.create(
            name=Notification.NotificationType.REMINDER,
            subject="Old",
            body="Old body",
        )

        self.client.force_login(
            self.admin,
        )


        response = self.client.post(
            reverse("notifications"),
            {
                "form-TOTAL_FORMS": "1",
                "form-INITIAL_FORMS": "1",
                "form-MIN_NUM_FORMS": "0",
                "form-MAX_NUM_FORMS": "1000",

                "form-0-id": notification.id,
                "form-0-name": "reminder",
                "form-0-subject": "New subject",
                "form-0-body": "New body",
            },
        )


        self.assertEqual(
            response.status_code,
            302,
        )


        notification.refresh_from_db()

        self.assertEqual(
            notification.subject,
            "New subject",
        )

    def test_reminders_without_campaign(self):

        Campaign.objects.all().delete()

        self.client.force_login(
            self.admin,
        )


        response = self.client.get(
            reverse("reminders"),
        )


        self.assertEqual(
            response.status_code,
            200,
        )


        self.assertEqual(
            response.context["user_years"],
            [],
        )

    def test_reminders_page(self):

        self.client.force_login(
            self.admin,
        )


        response = self.client.get(
            reverse("reminders"),
        )


        self.assertEqual(
            response.status_code,
            200,
        )


        self.assertEqual(
            len(response.context["user_years"]),
            2,
        )

    def test_reminders_filter_by_professor(self):

        self.client.force_login(
            self.admin,
        )


        response = self.client.get(
            reverse("reminders"),
            {
                "professor": self.user1.sciper,
            },
        )


        self.assertEqual(
            len(response.context["user_years"]),
            1,
        )


        self.assertEqual(
            response.context["user_years"][0].user,
            self.user1,
        )

    @patch("notifications.views.send_reminders")
    def test_send_reminders(self, mock_send):

        self.client.force_login(
            self.admin,
        )


        response = self.client.post(
            reverse("reminders"),
            {
                "send_reminder": [
                    self.user_year1.id,
                ],
            },
        )


        self.assertEqual(
            response.status_code,
            302,
        )


        self.user_year1.refresh_from_db()


        self.assertIsNotNone(
            self.user_year1.reminder_at,
        )


        mock_send.assert_called_once()

    @patch("notifications.views.send_reminders")
    def test_send_reminders_ignore_users_without_email(
        self,
        mock_send,
    ):

        self.client.force_login(
            self.admin,
        )

        response = self.client.post(
            reverse("reminders"),
            {
                "send_reminder": [
                    self.user_year2.id,
                ],
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.user_year2.refresh_from_db()

        self.assertIsNone(
            self.user_year2.reminder_at,
        )

        context = mock_send.call_args.args[0]

        self.assertEqual(
            context["bcc"],
            "",
        )

    def test_send_reminders_without_selection(self):

        self.client.force_login(
            self.admin,
        )


        response = self.client.post(
            reverse("reminders"),
            {},
        )


        self.assertEqual(
            response.status_code,
            302,
        )

    def test_reminders_campaign_closed_message(self):

        Campaign.objects.filter(
            id=self.campaign.id
        ).update(
            opening_date=timezone.now() - timedelta(days=10),
            closing_date=timezone.now() - timedelta(days=1),
        )

        self.client.force_login(
            self.admin,
        )

        response = self.client.get(
            reverse("reminders"),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        messages_list = list(
            response.wsgi_request._messages
        )

        self.assertEqual(
            len(messages_list),
            1,
        )

        self.assertEqual(
            str(messages_list[0]),
            "The campaign 2026 is closed",
        )
