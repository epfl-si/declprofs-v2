from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from campaigns.models import Campaign
from users.models import UserYear

User = get_user_model()


class CheckCampaignCommandTest(TestCase):

    def setUp(self):
        now = timezone.now()

        self.user = User.objects.create_user(
            username="prof1",
            sciper="123456",
            password="test",
        )

        self.user_year = UserYear.objects.create(
            user=self.user,
            year=now.year,
            is_eligible=True,
        )

    def test_no_campaign(self):
        out = StringIO()

        call_command("check_campaign", stdout=out)

        self.assertIn("No campaign found.", out.getvalue())

    def test_campaign_is_opening(self):
        now = timezone.now()

        campaign = Campaign.objects.create(
            year=now.year,
            opening_date=now - timedelta(days=3),
            closing_date=now + timedelta(days=3),
            was_opened=False,
        )

        self.assertTrue(campaign.is_open)

        out = StringIO()

        call_command("check_campaign", stdout=out)

        self.assertIn(
            f"Campaign {campaign.year} is currently open.",
            out.getvalue(),
        )

        self.assertIn(
            f"User years updated for campaign {campaign.year}.",
            out.getvalue(),
        )

        self.user_year.refresh_from_db()
        campaign.refresh_from_db()

        self.assertTrue(self.user_year.is_eligible)
        self.assertTrue(campaign.was_opened)

    def test_campaign_is_open(self):
        now = timezone.now()

        campaign = Campaign.objects.create(
            year=now.year,
            opening_date=now - timedelta(days=3),
            closing_date=now + timedelta(days=3),
        )

        out = StringIO()

        call_command("check_campaign", stdout=out)

        self.assertIn(
            f"Campaign {campaign.year} is currently open.",
            out.getvalue(),
        )

    def test_campaign_is_closed(self):
        now = timezone.now()

        campaign = Campaign.objects.create(
            year=now.year,
            opening_date=now - timedelta(days=6),
            closing_date=now - timedelta(days=3),
            was_opened=True,
        )

        self.assertFalse(campaign.is_open)

        out = StringIO()

        call_command("check_campaign", stdout=out)

        self.assertIn(
            f"Campaign {campaign.year} is closed.",
            out.getvalue(),
        )

        self.assertIn(
            f"User years updated for campaign {campaign.year}.",
            out.getvalue(),
        )

        self.user_year.refresh_from_db()
        campaign.refresh_from_db()

        self.assertFalse(self.user_year.is_eligible)
        self.assertFalse(campaign.was_opened)
