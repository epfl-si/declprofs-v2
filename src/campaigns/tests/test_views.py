from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from campaigns.models import Campaign
from campaigns.services import update_user_years_for_campaign
from users.models import UserYear


User = get_user_model()


class CampaignViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.admin = User.objects.create_superuser(
            username="admin",
            sciper="999999",
            password="password",
        )

        cls.user1 = User.objects.create_user(
            username="prof1",
            sciper="111111",
            password="password",
            has_access=True,
        )

        cls.user2 = User.objects.create_user(
            username="prof2",
            sciper="222222",
            password="password",
            has_access=True,
        )

        cls.campaign = Campaign.objects.create(
            year=2026,
            opening_date=timezone.now() - timedelta(days=1),
            closing_date=timezone.now() + timedelta(days=30),
            was_opened=False,
        )

        update_user_years_for_campaign(cls.campaign)

    def test_admin_can_view_campaign_page(self):

        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("campaign")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "campaigns/home.html",
        )

        self.assertIn(
            "campaign",
            response.context,
        )

        self.assertIn(
            "form",
            response.context,
        )

        self.assertIn(
            "rows",
            response.context,
        )

        self.assertIn(
            "years",
            response.context,
        )

        self.assertEqual(
            response.context["campaign"],
            self.campaign,
        )

    def test_non_admin_cannot_access_campaign_page(self):

        self.client.force_login(self.user1)

        response = self.client.get(reverse("campaign"))

        self.assertEqual(response.status_code, 403)

    def test_save_campaign_creates_user_years(self):

        # Remove generated UserYear records
        UserYear.objects.all().delete()

        self.client.force_login(
            self.admin,
        )

        response = self.client.post(
            reverse("campaign"),
            {
                "save_campaign": "",
                "year": 2026,
                "opening_date": (
                    timezone.now() - timedelta(days=1)
                ),
                "closing_date": (
                    timezone.now() + timedelta(days=30)
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertRedirects(
            response,
            f"{reverse('campaign')}?campaign_year=2026",
        )

        self.assertTrue(
            UserYear.objects.filter(
                user=self.user1,
                year=2026,
            ).exists()
        )

        self.assertTrue(
            UserYear.objects.filter(
                user=self.user2,
                year=2026,
            ).exists()
        )

    def test_save_eligibility_updates_user_years(self):

        user1_year = UserYear.objects.get(
            user=self.user1,
            year=2026,
        )

        user2_year = UserYear.objects.get(
            user=self.user2,
            year=2026,
        )

        # Initial state
        user1_year.is_eligible = False
        user1_year.save()

        user2_year.is_eligible = True
        user2_year.save()

        self.client.force_login(
            self.admin,
        )

        response = self.client.post(
            reverse("campaign"),
            {
                "save_eligibility": "",
                f"eligible_{user1_year.id}": "on",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertRedirects(
            response,
            reverse("campaign"),
        )

        user1_year.refresh_from_db()
        user2_year.refresh_from_db()

        self.assertTrue(
            user1_year.is_eligible,
        )

        self.assertFalse(
            user2_year.is_eligible,
        )

    def test_filter_by_professor(self):

        self.client.force_login(
            self.admin,
        )

        response = self.client.get(
            reverse("campaign"),
            {
                "professor": self.user1.sciper,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        rows = response.context["rows"]

        self.assertEqual(
            len(rows),
            1,
        )

        self.assertEqual(
            rows[0]["user"],
            self.user1,
        )

    def test_filter_by_year(self):

        UserYear.objects.create(
            user=self.user1,
            year=2025,
            is_eligible=True,
        )

        self.client.force_login(
            self.admin,
        )

        response = self.client.get(
            reverse("campaign"),
            {
                "year": "2025",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.context["years"],
            [2025],
        )

        rows = response.context["rows"]

        self.assertEqual(
            len(rows),
            User.objects.count(),
        )

        user1_row = next(
            row
            for row in rows
            if row["user"] == self.user1
        )

        self.assertIsNotNone(
            user1_row["years"][0],
        )

        self.assertEqual(
            user1_row["years"][0].year,
            2025,
        )

    def test_existing_user_year_is_updated(self):

        user_year = UserYear.objects.get(
            user=self.user1,
            year=2026,
        )

        # Initial state:
        # campaign is open, but we force an opposite value
        user_year.is_eligible = False
        user_year.save()

        closed_campaign = Campaign.objects.create(
            year=2027,
            opening_date=timezone.now() - timedelta(days=30),
            closing_date=timezone.now() - timedelta(days=1),
            was_opened=True,
        )

        user_year_2027 = UserYear.objects.create(
            user=self.user1,
            year=2027,
            is_eligible=True,
        )

        update_user_years_for_campaign(
            closed_campaign,
        )

        user_year_2027.refresh_from_db()

        self.assertFalse(
            user_year_2027.is_eligible,
        )

    def test_campaign_str(self):

        campaign = Campaign.objects.create(
            year=2030,
            opening_date=timezone.now() - timedelta(days=1),
            closing_date=timezone.now() + timedelta(days=30),
        )

        self.assertEqual(
            str(campaign),
            "Campaign 2030",
        )

    def test_existing_campaign(self):
        campaign = Campaign.objects.create(
            year=2025,
            opening_date=timezone.make_aware(datetime(2025, 1, 1, 9, 0, 0)),
            closing_date=timezone.make_aware(datetime(2025, 12, 31, 17, 0, 0)),
        )

        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("campaign_by_year"),
            {"year": 2025},
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json(),
            {
                "exists": True,
                "year": 2025,
                "opening_date": campaign.opening_date.strftime(
                    "%Y-%m-%dT%H:%M:%S"
                ),
                "closing_date": campaign.closing_date.strftime(
                    "%Y-%m-%dT%H:%M:%S"
                ),
                "is_open": campaign.is_open,
            },
        )

    def test_non_existing_campaign(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("campaign_by_year"),
            {"year": 2030},
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json(),
            {
                "exists": False,
                "year": 2030,
            },
        )

    def test_invalid_year(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("campaign_by_year"),
            {"year": "abc"},
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json(),
            {"exists": False},
        )

    def test_missing_year(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("campaign_by_year"),
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json(),
            {"exists": False},
        )

    def test_non_superuser_cannot_access_view(self):
        self.client.force_login(self.user1)

        response = self.client.get(
            reverse("campaign_by_year"),
            {"year": 2025},
        )

        self.assertEqual(response.status_code, 403)