from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from activities.models import Activity
from campaigns.models import Campaign
from campaigns.services import update_user_years_for_campaign
from users.models import UserYear

User = get_user_model()


class ActivityViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("import_email_templates")

    def setUp(self):

        self.user = User.objects.create_user(
            username="prof",
            sciper="123456",
            password="password",
            has_access=True,
        )

        self.admin = User.objects.create_superuser(
            username="admin",
            sciper="999999",
            password="password",
            has_access=True,
        )
        
        campaign = Campaign.objects.create(
            year=2026,
            opening_date=timezone.now() - timedelta(days=1),
            closing_date=timezone.now() + timedelta(days=30),
        )

        update_user_years_for_campaign(campaign)

    def test_create_activity(self):

        self.client.force_login(self.user)

        response = self.client.post(
            reverse("home"),
            {
                "action": "create",
                "user": self.user.id,
                "activity": "Teaching",
                "principal": "EPFL",
                "comments": "",
                "date_start": "2026-01-01",
                "date_end": "",
            },
        )

        user_year = UserYear.objects.get(user=self.user)

        self.assertEqual(user_year.draft_count, 1)
        self.assertEqual(user_year.submitted_count, 0)
        self.assertEqual(user_year.missing_count, 0)

    def test_submit_drafts(self):

        self.client.force_login(self.user)

        self.client.post(
            reverse("home"),
            {
                "action": "create",
                "user": self.user.id,
                "activity": "Research",
                "principal": "MIT",
                "comments": "Updated",
                "date_start": "2026-02-01",
                "date_end": "",
            },
        )

        response = self.client.post(
            reverse("home"),
            {
                "action": "confirm_submit_drafts",
            },
        )

        user_year = UserYear.objects.get(user=self.user)

        self.assertEqual(user_year.draft_count, 0)
        self.assertEqual(user_year.submitted_count, 1)
        self.assertEqual(user_year.missing_count, 0)

    def test_delete_activity_draft(self):

        self.client.force_login(self.user)

        self.client.post(
            reverse("home"),
            {
                "action": "create",
                "user": self.user.id,
                "activity": "Research",
                "principal": "MIT",
                "comments": "Updated",
                "date_start": "2026-02-01",
                "date_end": "",
            },
        )

        activity = Activity.objects.get(user=self.user)

        self.client.post(
            reverse("home"),
            {
                "action": "delete",
                "activity_id": activity.id,
            },
        )

        user_year = UserYear.objects.get(user=self.user)

        self.assertEqual(user_year.draft_count, 0)
        self.assertEqual(user_year.submitted_count, 0)
        self.assertEqual(user_year.missing_count, 1)

    def test_delete_activity_submitted(self):

        self.client.force_login(self.user)

        self.client.post(
            reverse("home"),
            {
                "action": "create",
                "user": self.user.id,
                "activity": "Research",
                "principal": "MIT",
                "comments": "Updated",
                "date_start": "2026-02-01",
                "date_end": "",
            },
        )

        self.client.post(
            reverse("home"),
            {
                "action": "confirm_submit_drafts",
            },
        )

        activity = Activity.objects.get(user=self.user)

        self.client.post(
            reverse("home"),
            {
                "action": "delete",
                "activity_id": activity.id,
            },
        )

        user_year = UserYear.objects.get(user=self.user)

        self.assertEqual(user_year.draft_count, 0)
        self.assertEqual(user_year.submitted_count, 0)
        self.assertEqual(user_year.missing_count, 1)

    def test_duplicate_same_year_activity_submitted(self):

        self.client.force_login(self.user)

        self.client.post(
            reverse("home"),
            {
                "action": "create",
                "user": self.user.id,
                "activity": "Research",
                "principal": "MIT",
                "comments": "Updated",
                "date_start": "2026-02-01",
                "date_end": "",
            },
        )

        self.client.post(
            reverse("home"),
            {
                "action": "confirm_submit_drafts",
            },
        )

        activity = Activity.objects.get(user=self.user)

        self.client.post(
            reverse("home"),
            {
                "action": "duplicate",
                "activity_id": activity.id,
            },
        )

        user_year = UserYear.objects.get(user=self.user)
        
        self.assertEqual(user_year.draft_count, 1)
        self.assertEqual(user_year.submitted_count, 1)
        self.assertEqual(user_year.missing_count, 0)


    def test_save_changed_activity_submitted(self):

        campaign_2025 = Campaign.objects.first()
        campaign_2025.year = 2025
        campaign_2025.save()

        update_user_years_for_campaign(campaign_2025)

        user_year_2025 = UserYear.objects.get(user=self.user, year=2025)
                
        self.assertEqual(user_year_2025.draft_count, 0)
        self.assertEqual(user_year_2025.submitted_count, 0)
        self.assertEqual(user_year_2025.missing_count, 1)

        self.client.force_login(self.user)

        self.client.post(
            reverse("home"),
            {
                "action": "create",
                "user": self.user.id,
                "activity": "Research",
                "principal": "MIT",
                "comments": "Updated",
                "date_start": "2026-02-01",
                "date_end": "",
            },
        )

        self.client.post(
            reverse("home"),
            {
                "action": "confirm_submit_drafts",
            },
        )

        activity = Activity.objects.get(user=self.user)

        self.client.post(
            reverse("home"),
            {
                "action": "save",
                "activity_id": activity.id,
                "user": self.user.id,
                "activity": "Research",
                "principal": "MIT",
                "comments": "Updated",
                "date_start": "2025-02-01",
                "date_end": "",
            },
        )

        user_year_2026 = UserYear.objects.get(user=self.user, year=2026)

        self.assertEqual(user_year_2026.draft_count, 0)
        self.assertEqual(user_year_2026.submitted_count, 1)
        self.assertEqual(user_year_2026.missing_count, 0)

        user_year_2025 = UserYear.objects.get(user=self.user, year=2025)
        
        self.assertEqual(user_year_2025.draft_count, 0)
        self.assertEqual(user_year_2025.submitted_count, 1)
        self.assertEqual(user_year_2025.missing_count, 0)

    def test_save_changed_activity_submitted_year_not_eligible(self):

        self.client.force_login(self.user)

        self.client.post(
            reverse("home"),
            {
                "action": "create",
                "user": self.user.id,
                "activity": "Research",
                "principal": "MIT",
                "comments": "Updated",
                "date_start": "2026-02-01",
                "date_end": "",
            },
        )

        self.client.post(
            reverse("home"),
            {
                "action": "confirm_submit_drafts",
            },
        )

        activity = Activity.objects.get(user=self.user)

        response = self.client.post(
            reverse("home"),
            {
                "action": "save",
                "activity_id": activity.id,
                "user": self.user.id,
                "activity": "Research",
                "principal": "MIT",
                "comments": "Updated",
                "date_start": "2025-02-01",
                "date_end": "",
            },
        )

        self.assertEqual(response.status_code, 200)

        form = response.context["form"]

        self.assertTrue(form.non_field_errors())
        self.assertIn("The campaign 2025 is closed", form.non_field_errors())

        response = self.client.post(
            reverse("home"),
            {
                "action": "save",
                "activity_id": activity.id,
                "user": self.user.id,
                "activity": "Research",
                "principal": "MIT",
                "comments": "Updated",
                "date_start": "2024-02-01",
                "date_end": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        
        form = response.context["form"]

        self.assertTrue(form.non_field_errors())
        self.assertIn("The campaign years 2024, 2025 are closed", form.non_field_errors())
