from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
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

    def test_home_requires_authentication(self):
        response = self.client.get(
            reverse("home"),
        )

        # redirect to /auth/authenticate?next=/
        self.assertEqual(
            response.status_code,
            302,
        )

    def test_create_activity_adds_draft_counter(self):

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

        self.assertEqual(
            response.status_code,
            302,
        )

        activity = Activity.objects.first()

        self.assertIsNotNone(activity)

        self.assertEqual(
            activity.user,
            self.user,
        )

        user_year = UserYear.objects.get(user=self.user)

        self.assertEqual(
            user_year.draft_count,
            1,
        )

        self.assertEqual(
            user_year.missing_count,
            0,
        )

    def test_duplicate_activity(self):

        activity = Activity.objects.create(
            user=self.user,
            activity="Teaching",
            principal="EPFL",
            date_start="2026-01-01",
        )

        self.client.force_login(
            self.user,
        )

        response = self.client.post(
            reverse("home"),
            {
                "action": "duplicate",
                "activity_id": activity.id,
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            Activity.objects.count(),
            2,
        )

        duplicated = Activity.objects.exclude(
            id=activity.id,
        ).first()

        self.assertEqual(
            duplicated.activity,
            activity.activity,
        )

        self.assertEqual(
            duplicated.principal,
            activity.principal,
        )

        self.assertTrue(
            duplicated.is_draft,
        )

        self.assertIsNone(
            duplicated.date_end,
        )

    def test_save_activity(self):

        activity = Activity.objects.create(
            user=self.user,
            activity="Teaching",
            principal="EPFL",
            comments="Old comment",
            date_start="2026-01-01",
        )

        self.client.force_login(
            self.user,
        )

        response = self.client.post(
            reverse("home"),
            {
                "action": "save",
                "activity_id": activity.id,
                "user": self.user.id,
                "activity": "Research",
                "principal": "MIT",
                "comments": "Updated",
                "date_start": "2026-02-01",
                "date_end": "",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        activity.refresh_from_db()

        self.assertEqual(
            activity.activity,
            "Research",
        )

        self.assertEqual(
            activity.principal,
            "MIT",
        )

        self.assertEqual(
            activity.comments,
            "Updated",
        )

    def test_submit_drafts_renders_confirmation_for_user(self):

        self.client.force_login(self.user)

        Activity.objects.create(
            user=self.user,
            activity="Teaching",
            principal="EPFL",
            date_start="2026-01-01",
        )

        response = self.client.post(
            reverse("home"),
            {
                "action": "submit_drafts",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "activities/confirm_submission.html",
        )

        self.assertEqual(
            response.context["current_user"],
            self.user,
        )

        self.assertEqual(
            response.context["drafts_count"],
            1,
        )

    def test_submit_drafts_redirects_when_no_draft_exists(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("home"),
            {
                "action": "submit_drafts",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            f"{reverse('home')}?professor={self.user.sciper}",
        )

        messages = list(response.wsgi_request._messages)

        self.assertEqual(
            str(messages[0]),
            "There are no draft activities to submit for 2026.",
        )

    def test_superuser_submit_drafts_for_professor(self):

        self.client.force_login(self.admin)

        Activity.objects.create(
            user=self.user,
            activity="Research",
            principal="MIT",
            date_start="2026-01-01",
        )

        response = self.client.post(
            reverse("home"),
            {
                "action": "submit_drafts",
                "professor": self.user.sciper,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "activities/confirm_submission.html",
        )

        self.assertEqual(
            response.context["current_user"],
            self.user,
        )

        self.assertEqual(
            response.context["drafts_count"],
            1,
        )

    def test_superuser_submit_drafts_requires_professor(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("home"),
            {
                "action": "submit_drafts",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("home"),
        )

        messages = list(response.wsgi_request._messages)

        self.assertEqual(
            str(messages[0]),
            "Please select a professor.",
        )

    def test_superuser_submit_drafts_invalid_professor(self):

        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("home"),
            {
                "action": "submit_drafts",
                "professor": "222222",
            },
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_submit_drafts_confirmation_page(self):

        Activity.objects.create(
            user=self.user,
            activity="Teaching",
            principal="EPFL",
            date_start="2026-01-01",
        )

        self.client.force_login(
            self.user,
        )

        response = self.client.post(
            reverse("home"),
            {
                "action": "submit_drafts",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "activities/confirm_submission.html",
        )

        self.assertEqual(
            response.context["drafts_count"],
            1,
        )

        self.assertEqual(
        response.context["current_user"],
        self.user,
    )

    def test_submit_drafts_as_admin(self):

        self.client.force_login(self.admin)

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

        messages = list(response.wsgi_request._messages)

        self.assertEqual(
            str(messages[0]),
            "Please select a professor.",
        )

        response = self.client.post(
            f"{reverse('home')}?professor={self.user.sciper}",
            {
                "action": "confirm_submit_drafts",
            },
        )

        activity = Activity.objects.get(user=self.user)

        self.assertTrue(activity.is_submitted)

    def test_submit_drafts_updates_counters(self):

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

        response = self.client.post(
            reverse("home"),
            {
                "action": "confirm_submit_drafts",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        activity.refresh_from_db()

        self.assertTrue(activity.is_submitted)

        user_year = UserYear.objects.get(user=self.user)

        self.assertEqual(
            user_year.draft_count,
            0,
        )

        self.assertEqual(
            user_year.submitted_count,
            1,
        )

    def test_delete_activity_draft_updates_counter(self):

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

        user_year = UserYear.objects.get(user=self.user)

        response = self.client.post(
            reverse("home"),
            {
                "action": "delete",
                "activity_id": activity.id,
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertFalse(
            Activity.objects.filter(
                id=activity.id
            ).exists()
        )

        user_year.refresh_from_db()

        self.assertEqual(
            user_year.draft_count,
            0,
        )

        self.assertEqual(
            user_year.missing_count,
            1,
        )

    def test_delete_activity_submitted_updates_counter(self):

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

        self.assertEqual(
            user_year.missing_count,
            1,
        )

        self.assertEqual(
            user_year.draft_count,
            0,
        )

        self.assertEqual(
            user_year.submitted_count,
            0,
        )

    def test_user_cannot_delete_other_user_activity(self):

        other = User.objects.create_user(
            username="other",
            sciper="222222",
            password="password",
        )

        activity = Activity.objects.create(
            user=other,
            activity="Secret",
            principal="EPFL",
            date_start="2026-01-01",
        )

        self.client.force_login(self.user)

        response = self.client.post(
            reverse("home"),
            {
                "action": "delete",
                "activity_id": activity.id,
            },
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_user_delete_ineligible_activity_shows_error_message(self):
        activity = Activity.objects.create(
            user=self.user,
            activity="Research",
            principal="EPFL",
            date_start="2026-01-01",
        )

        self.client.force_login(self.user)

        expected_message = "Certaines années ne sont pas éligibles."

        with patch(
            "activities.views.check_eligibility",
            return_value=([], expected_message),
        ):
            response = self.client.post(
                reverse("home"),
                {
                    "action": "delete",
                    "activity_id": activity.id,
                },
            )

        self.assertEqual(response.status_code, 302)

        messages = list(get_messages(response.wsgi_request))
        self.assertIn(
            expected_message,
            [str(message) for message in messages],
        )

        self.assertTrue(
            Activity.objects.filter(pk=activity.pk).exists()
        )

    def test_superuser_delete_ineligible_activity_shows_error_message(self):
        activity = Activity.objects.create(
            user=self.user,
            activity="Research",
            principal="EPFL",
            date_start="2026-01-01",
        )

        self.client.force_login(self.admin)

        expected_message = "Certaines années ne sont pas éligibles."

        with patch(
            "activities.views.check_eligibility",
            return_value=([], expected_message),
        ):
            response = self.client.post(
                reverse("home"),
                {
                    "action": "delete",
                    "activity_id": activity.id,
                },
            )

        self.assertEqual(response.status_code, 302)

        messages = list(get_messages(response.wsgi_request))
        self.assertIn(
            expected_message,
            [str(message) for message in messages],
        )

        self.assertTrue(Activity.objects.filter(pk=activity.pk).exists())

        self.assertIn(f"professor={self.user.sciper}", response.url)

    def test_superuser_delete_ineligible_activity_preserves_url_params(self):
        activity = Activity.objects.create(
            user=self.user,
            activity="Research",
            principal="EPFL",
            date_start="2026-01-01",
        )

        self.client.force_login(self.admin)

        expected_message = "Certaines années ne sont pas éligibles."

        with patch(
            "activities.views.check_eligibility",
            return_value=([], expected_message),
        ):
            response = self.client.post(
                reverse("home"),
                {
                    "action": "delete",
                    "activity_id": activity.id,
                    "year": "2026",
                    "page": "3",
                },
            )

        self.assertEqual(response.status_code, 302)

        self.assertEqual(
            response.url,
            f"{reverse('home')}?professor={self.user.sciper}"
            f"&year=2026&id={activity.id}&page=3",
        )

        messages = list(get_messages(response.wsgi_request))
        self.assertIn(
            expected_message,
            [str(message) for message in messages],
        )

        self.assertTrue(
            Activity.objects.filter(pk=activity.pk).exists()
        )

    def test_superuser_can_filter_by_professor(self):

        other = User.objects.create_user(
            username="other",
            sciper="222222",
            password="password",
        )

        Activity.objects.create(
            user=other,
            activity="Secret",
            principal="EPFL",
            date_start="2026-01-01",
        )

        Activity.objects.create(
            user=self.user,
            activity="Secret",
            principal="EPFL",
            date_start="2026-01-01",
        )

        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("home"),
        )

        activities = response.context["activities"]

        self.assertEqual(
            activities.count(),
            2,
        )

        response = self.client.get(
            reverse("home"),
            {
                "professor": self.user.sciper,
            },
        )

        activities = response.context["activities"]

        self.assertEqual(
            activities.count(),
            1,
        )

        self.assertEqual(
            activities.first().user,
            self.user,
        )

    def test_normal_user_cannot_filter_other_professor(self):

        other = User.objects.create_user(
            username="other",
            sciper="222222",
            password="password",
        )

        Activity.objects.create(
            user=other,
            activity="Secret",
            principal="EPFL",
            date_start="2026-01-01",
        )

        self.client.force_login(self.user)

        response = self.client.get(
            reverse("home"),
        )

        activities = response.context["activities"]

        self.assertEqual(
            activities.count(),
            0,
        )

        response = self.client.get(
            reverse("home"),
            {
                "professor": other.sciper,
            },
        )

        activities = response.context["activities"]

        self.assertEqual(
            activities.count(),
            0,
        )

    def test_filter_by_valid_year(self):

        Activity.objects.create(
            user=self.user,
            activity="Teacher",
            principal="EPFL",
            date_start="2026-01-01",
        )

        Activity.objects.create(
            user=self.user,
            activity="Teacher",
            principal="EPFL",
            date_start="2026-01-01",
            date_end="2025-11-01",
        )

        Activity.objects.create(
            user=self.user,
            activity="Secret",
            principal="EPFL",
            date_start="2025-01-01",
        )

        self.client.force_login(self.user)

        response = self.client.get(
            reverse("home"),
        )

        activities = response.context["activities"]

        self.assertEqual(
            activities.count(),
            3,
        )

        response = self.client.get(
            reverse("home"),
            {
                "year": "2026",
            },
        )

        activities = response.context["activities"]

        self.assertEqual(
            activities.count(),
            2,
        )

    def test_invalid_year_is_ignored(self):

        Activity.objects.create(
            user=self.user,
            activity="Teacher",
            principal="EPFL",
            date_start="2026-01-01",
        )

        Activity.objects.create(
            user=self.user,
            activity="Secret",
            principal="EPFL",
            date_start="2025-01-01",
        )

        self.client.force_login(self.user)

        response = self.client.get(
            reverse("home"),
        )

        activities = response.context["activities"]

        self.assertEqual(
            activities.count(),
            2,
        )        

        response = self.client.get(
            reverse("home"),
            {
                "year": "abcd",
            },
        )

        activities = response.context["activities"]

        self.assertEqual(
            activities.count(),
            2,
        )


    def test_get_activity_by_id_loads_form_instance(self):

        activity = Activity.objects.create(
            user=self.user,
            activity="Teacher",
            principal="EPFL",
            date_start="2026-01-01",
        )
    
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("home"),
            {
                "id": activity.id,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        selected_activity = response.context["selected_activity"]

        self.assertEqual(
            selected_activity,
            activity,
        )

        self.assertEqual(
            response.context["form"].instance,
            activity,
        )
