from datetime import timedelta
from unittest.mock import patch

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


class ActivityReportingTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("import_email_templates")

    def setUp(self):

        self.admin = User.objects.create_superuser(
            username="admin",
            sciper="999999",
            password="password",
        )

        self.user = User.objects.create_user(
            username="prof",
            sciper="123456",
            password="password",
            first_name="John",
            last_name="Doe",
            email="john@epfl.ch",
            unit="IC",
            has_access=True,
        )

        Activity.objects.create(
            user=self.user,
            activity="Teaching",
            principal="EPFL",
            comments="None",
            date_start="2026-01-01",
        )

        UserYear.objects.create(
            user=self.user,
            year=2026,
            is_eligible=True,
        )

    def test_user_cannot_access_disclosure_report(self):

        self.client.force_login(
            self.user,
        )

        response = self.client.get(
            reverse("disclosure_report"),
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_disclosure_report_requires_professor_and_year(self):

        self.client.force_login(
            self.admin,
        )

        response = self.client.get(
            reverse("disclosure_report"),
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertRedirects(
            response,
            reverse("home"),
        )

    @patch("activities.views.HTML")
    def test_disclosure_report_returns_pdf(
        self,
        mock_html,
    ):

        mock_html.return_value.write_pdf.return_value = b"PDF"

        self.client.force_login(
            self.admin,
        )

        response = self.client.get(
            reverse("disclosure_report"),
            {
                "professor": self.user.sciper,
                "year": 2026,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response["Content-Type"],
            "application/pdf",
        )

        self.assertIn(
            "123456-2026.pdf",
            response["Content-Disposition"],
        )

        self.assertEqual(
            response.content,
            b"PDF",
        )

    def test_report_csv_requires_year(self):

        self.client.force_login(
            self.admin,
        )

        response = self.client.get(
            reverse("report_csv"),
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertRedirects(
            response,
            reverse("home"),
        )

    def test_report_csv_single_professor(self):

        self.client.force_login(
            self.admin,
        )

        response = self.client.get(
            reverse("report_csv"),
            {
                "professor": self.user.sciper,
                "year": 2026,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response["Content-Type"],
            "text/csv; charset=utf-8",
        )

        self.assertIn(
            "123456-2026.csv",
            response["Content-Disposition"],
        )

        content = response.content.decode("utf-8")

        self.assertIn(
            "Teaching",
            content,
        )

        self.assertIn(
            "EPFL",
            content,
        )

        self.assertIn(
            "123456",
            content,
        )

    def test_report_csv_all_professors(self):

        other = User.objects.create_user(
            username="other",
            sciper="654321",
            password="password",
        )

        Activity.objects.create(
            user=other,
            activity="Research",
            principal="MIT",
            date_start="2026-02-01",
        )

        self.client.force_login(
            self.admin,
        )

        response = self.client.get(
            reverse("report_csv"),
            {
                "year": 2026,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertIn(
            "all-professors-2026.csv",
            response["Content-Disposition"],
        )

        content = response.content.decode("utf-8")

        self.assertIn(
            "Teaching",
            content,
        )

        self.assertIn(
            "Research",
            content,
        )

    def test_report_csv_filters_by_year(self):

        Activity.objects.create(
            user=self.user,
            activity="Old activity",
            principal="Old",
            date_start="2025-01-01",
            date_end="2025-12-31",
        )

        self.client.force_login(
            self.admin,
        )

        response = self.client.get(
            reverse("report_csv"),
            {
                "year": 2026,
            },
        )

        content = response.content.decode("utf-8")

        self.assertNotIn(
            "Old activity",
            content,
        )

        self.assertIn(
            "Teaching",
            content,
        )
