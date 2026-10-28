from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from users.models import UserYear

User = get_user_model()


class UserYearViewTest(TestCase):

    def setUp(self):

        self.admin = User.objects.create_superuser(
            username="admin",
            sciper="999999",
            password="password",
        )

        self.prof1 = User.objects.create_user(
            username="prof1",
            first_name="John",
            last_name="Doe",
            sciper="111111",
        )

        self.prof2 = User.objects.create_user(
            username="prof2",
            first_name="Jane",
            last_name="Smith",
            sciper="222222",
        )

        self.user_year1 = UserYear.objects.create(
            user=self.prof1,
            year=2026,
            is_eligible=True,
            submitted_count=1,
            draft_count=0,
            missing_count=0,
        )

        self.user_year2 = UserYear.objects.create(
            user=self.prof2,
            year=2026,
            is_eligible=True,
            submitted_count=0,
            draft_count=1,
            missing_count=0,
        )

        self.user_year3 = UserYear.objects.create(
            user=self.prof2,
            year=2025,
            is_eligible=True,
            submitted_count=0,
            draft_count=0,
            missing_count=1,
        )

    def test_home_requires_superuser(self):

        self.prof1.has_access = True
        self.prof1.save()

        self.client.force_login(self.prof1)

        response = self.client.get(reverse("users"))

        self.assertEqual(response.status_code, 403)

    def test_home_allows_superuser(self):

        self.client.force_login(self.admin)

        response = self.client.get(reverse("users"))

        self.assertEqual(response.status_code, 200)

    def test_home_displays_user_years(self):

        self.client.force_login(self.admin)

        response = self.client.get(reverse("users"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/home.html")
        self.assertEqual(response.context["selected_year"], "2026")
        self.assertEqual(response.context["user_years"].count(), 2)


    def test_home_year_filter(self):

        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("users"),
            {
                "year": "2025",
            },
        )

        self.assertEqual(response.context["selected_year"], "2025")
        self.assertEqual(response.context["user_years"].count(), 1)
        self.assertEqual(response.context["user_years"].first(), self.user_year3)


    def test_filter_by_professor(self):

        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("users"),
            {
                "professor": "111111",
            },
        )

        user_years = response.context["user_years"]

        self.assertEqual(user_years.count(), 1)
        self.assertEqual(user_years.first(), self.user_year1)


    def test_filter_exempted_users(self):

        self.user_year1.is_exempted = True
        self.user_year1.save()

        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("users"),
            {
                "exempted": "1",
            },
        )

        self.assertEqual(response.context["user_years"].count(), 1)
        self.assertEqual(response.context["user_years"].first(), self.user_year1)


    def test_filter_submitted_status(self):

        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("users"),
            {
                "status": "submitted",
            },
        )

        self.assertEqual(response.context["user_years"].count(), 1)
        self.assertEqual(response.context["user_years"].first(), self.user_year1)


    def test_filter_incomplete_status(self):

        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("users"),
            {
                "status": "incomplete",
            },
        )

        self.assertEqual(response.context["user_years"].count(), 1)
        self.assertEqual(response.context["user_years"].first(), self.user_year2)


    def test_filter_missing_status(self):

        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("users"),
            {
                "year": "2025",
                "status": "missing",
            },
        )

        self.assertEqual(response.context["user_years"].count(), 1)
        self.assertEqual(response.context["user_years"].first(), self.user_year3)


    def test_stats_are_correct(self):

        self.client.force_login(self.admin)

        response = self.client.get(reverse("users"))

        stats = response.context["stats"]

        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["submitted"], 1)
        self.assertEqual(stats["incomplete"], 1)
        self.assertEqual(stats["missings"], 0)


    def test_post_updates_eligibility_and_exemption(self):

        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("users"),
            {
                "user_year_ids": [self.user_year1.id],
                f"eligible_{self.user_year1.id}": "on",
                f"exempted_{self.user_year1.id}": "on",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.user_year1.refresh_from_db()

        self.assertFalse(self.user_year1.is_eligible)

        self.assertTrue(self.user_year1.is_exempted)