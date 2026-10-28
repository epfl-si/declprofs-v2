from datetime import date, datetime

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.timezone import get_current_timezone, make_aware, is_naive

from activities.models import Activity
from auditlogs.models import ActivityLog

User = get_user_model()


@override_settings(PAGINATION_LOGS=2)
class ActivityLogViewTest(TestCase):

    def setUp(self):
        # --------------------------------------------------
        # Users
        # --------------------------------------------------

        self.admin = User.objects.create_superuser(
            username="admin",
            password="password",
            sciper="999999",
        )

        self.prof1 = User.objects.create_user(
            username="prof1",
            first_name="John",
            last_name="Doe",
            password="password",
            sciper="111111",
        )

        self.prof2 = User.objects.create_user(
            username="prof2",
            first_name="Jane",
            last_name="Smith",
            password="password",
            sciper="222222",
        )

        # --------------------------------------------------
        # Activities
        # --------------------------------------------------

        self.activity1 = Activity.objects.create(
            user=self.prof1,
            activity="Publication scientifique",
            principal="Projet de recherche A",
            date_start=date(2026, 1, 1),
        )

        self.activity2 = Activity.objects.create(
            user=self.prof2,
            activity="Conférence internationale",
            principal="Projet de recherche B",
            date_start=date(2026, 2, 1),
        )

        # --------------------------------------------------
        # Actions
        # --------------------------------------------------

        self.action1 = ActivityLog.Action.choices[0][0]

        self.action2 = (
            ActivityLog.Action.choices[1][0]
            if len(ActivityLog.Action.choices) > 1
            else self.action1
        )

        # --------------------------------------------------
        # Logs
        # --------------------------------------------------

        self.log1 = self.create_log(
            user=self.prof1,
            activity=self.activity1,
            action=self.action1,
            changes={},
            created_at=make_aware(
                datetime(2026, 1, 10, 10, 0),
                get_current_timezone()
            )
        )

        self.log2 = self.create_log(
            user=self.prof2,
            activity=self.activity2,
            action=self.action2,
            changes={},
            created_at=make_aware(
                datetime(2026, 2, 15, 14, 30),
                get_current_timezone()
            )
        )

        self.log3 = self.create_log(
            user=self.prof1,
            activity=self.activity2,
            action=self.action1,
            changes={},
            created_at=make_aware(
                datetime(2026, 3, 20, 16, 0),
                get_current_timezone()
            )
        )

    # ======================================================
    # Helpers
    # ======================================================

    def create_log(
        self,
        user,
        activity,
        action,
        changes=None,
        created_at=None,
    ):
        log = ActivityLog.objects.create(
            user=user,
            activity=activity,
            action=action,
            changes=changes or {},
        )

        if created_at is not None:
            if is_naive(created_at):
                created_at = make_aware(created_at)

            ActivityLog.objects.filter(pk=log.pk).update(
                created_at=created_at,
            )

            log.refresh_from_db()

        return log

    def get_logs(self, response):
        """
        Retourne les logs de la page courante.
        """
        return response.context["page_obj"].object_list

    def get_all_logs(self, response):
        """
        Retourne tous les logs correspondant aux filtres,
        sans se limiter à la page courante.
        """
        return response.context["page_obj"].paginator.object_list

    def login_admin(self):
        self.client.force_login(self.admin)

    # ======================================================
    # Access
    # ======================================================

    def test_superuser_can_access_view(self):
        self.login_admin()

        response = self.client.get(reverse("auditlogs"))

        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_cannot_access_view(self):
        response = self.client.get(reverse("auditlogs"))

        self.assertNotEqual(response.status_code, 200)

    def test_regular_user_cannot_access_view(self):
        self.client.force_login(self.prof1)

        response = self.client.get(reverse("auditlogs"))

        self.assertNotEqual(response.status_code, 200)

    # ======================================================
    # Basic rendering
    # ======================================================

    def test_view_uses_correct_template(self):
        self.login_admin()

        response = self.client.get(reverse("auditlogs"))

        self.assertTemplateUsed(response, "auditlogs/home.html")

    def test_view_returns_expected_context(self):
        self.login_admin()

        response = self.client.get(reverse("auditlogs"))

        self.assertIn("page_obj", response.context)
        self.assertIn("users", response.context)
        self.assertIn("date_from", response.context)
        self.assertIn("date_to", response.context)
        self.assertIn("performed_by", response.context)
        self.assertIn("owner", response.context)
        self.assertIn("action", response.context)
        self.assertIn("activity_search", response.context)
        self.assertIn("action_choices", response.context)

    def test_all_logs_are_displayed_without_filters(self):
        self.login_admin()

        response = self.client.get(reverse("auditlogs"))

        self.assertEqual(
            response.context["page_obj"].paginator.count,
            3,
        )

    def test_users_are_ordered_by_last_name_and_first_name(self):
        self.login_admin()

        response = self.client.get(reverse("auditlogs"))

        users = list(response.context["users"])

        self.assertEqual(
            users,
            sorted(
                [self.admin, self.prof1, self.prof2],
                key=lambda user: (
                    user.last_name,
                    user.first_name,
                ),
            ),
        )

    # ======================================================
    # Date filters
    # ======================================================

    def test_filter_by_date_from(self):
        self.login_admin()

        response = self.client.get(
            reverse("auditlogs"),
            {"date_from": "2026-02-01"},
        )

        self.assertEqual(
            response.context["page_obj"].paginator.count,
            2,
        )

        self.assertEqual(
            response.context["date_from"],
            "2026-02-01",
        )

    def test_filter_by_date_to(self):
        self.login_admin()

        response = self.client.get(
            reverse("auditlogs"),
            {"date_to": "2026-02-28"},
        )

        self.assertEqual(
            response.context["page_obj"].paginator.count,
            2,
        )

        self.assertEqual(
            response.context["date_to"],
            "2026-02-28",
        )

    def test_filter_by_date_range(self):
        self.login_admin()

        response = self.client.get(
            reverse("auditlogs"),
            {
                "date_from": "2026-02-01",
                "date_to": "2026-02-28",
            },
        )

        self.assertEqual(
            response.context["page_obj"].paginator.count,
            1,
        )

        self.assertEqual(
            list(self.get_logs(response)),
            [self.log2],
        )

    def test_invalid_date_from_is_ignored(self):
        self.login_admin()

        response = self.client.get(
            reverse("auditlogs"),
            {"date_from": "invalid-date"},
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.context["page_obj"].paginator.count,
            3,
        )

        self.assertEqual(response.context["date_from"], "")

    def test_invalid_date_to_is_ignored(self):
        self.login_admin()

        response = self.client.get(
            reverse("auditlogs"),
            {"date_to": "invalid-date"},
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.context["page_obj"].paginator.count,
            3,
        )

        self.assertEqual(response.context["date_to"], "")

    # ======================================================
    # Performed-by filter
    # ======================================================

    def test_filter_by_performed_by(self):
        self.login_admin()

        response = self.client.get(
            reverse("auditlogs"),
            {"performed_by": str(self.prof1.pk)},
        )

        self.assertEqual(
            response.context["page_obj"].paginator.count,
            2,
        )

        self.assertEqual(
            response.context["performed_by"],
            str(self.prof1.pk),
        )

        self.assertSetEqual(
            set(self.get_all_logs(response).values_list("id", flat=True)),
            {self.log1.pk, self.log3.pk},
        )

    def test_filter_by_unknown_performed_by_returns_no_logs(self):
        self.login_admin()

        response = self.client.get(
            reverse("auditlogs"),
            {"performed_by": "99999999"},
        )

        self.assertEqual(
            response.context["page_obj"].paginator.count,
            0,
        )

    # ======================================================
    # Owner filter
    # ======================================================

    def test_filter_by_activity_owner(self):
        self.login_admin()

        response = self.client.get(
            reverse("auditlogs"),
            {"owner": str(self.prof1.pk)},
        )

        self.assertEqual(
            response.context["page_obj"].paginator.count,
            1,
        )

        self.assertEqual(
            list(self.get_logs(response)),
            [self.log1],
        )

    def test_filter_by_owner_in_changes(self):
        self.login_admin()

        log = self.create_log(
            user=self.prof2,
            activity=self.activity2,
            action=self.action2,
            changes={"user_id": str(self.prof1.pk)},
            created_at=make_aware(
                datetime(2026, 4, 2, 12, 0),
                get_current_timezone()
            )
        )

        response = self.client.get(
            reverse("auditlogs"),
            {"owner": str(self.prof1.pk)},
        )

        self.assertEqual(response.status_code, 200)

        self.assertIn(
            log.pk,
            self.get_all_logs(response).values_list("id", flat=True),
        )

    # ======================================================
    # Action filter
    # ======================================================

    def test_filter_by_action(self):
        self.login_admin()

        response = self.client.get(
            reverse("auditlogs"),
            {"action": self.action2},
        )

        expected_ids = {
            self.log.pk
            for self.log in [self.log2]
            if self.log.action == self.action2
        }

        # Si les choix d'action ne comportent qu'une seule valeur,
        # tous les logs ont la même action dans ce jeu de données.
        if self.action1 == self.action2:
            expected_ids = {
                self.log1.pk,
                self.log2.pk,
                self.log3.pk,
            }

        self.assertSetEqual(
            set(self.get_all_logs(response).values_list("id", flat=True)),
            expected_ids,
        )

        self.assertEqual(
            response.context["action"],
            self.action2,
        )

    # ======================================================
    # Activity search
    # ======================================================

    def test_filter_by_activity_name(self):
        self.login_admin()

        response = self.client.get(
            reverse("auditlogs"),
            {"activity": "Publication"},
        )

        self.assertEqual(
            response.context["page_obj"].paginator.count,
            1,
        )

        self.assertEqual(
            list(self.get_logs(response)),
            [self.log1],
        )

    def test_activity_search_is_case_insensitive(self):
        self.login_admin()

        response = self.client.get(
            reverse("auditlogs"),
            {"activity": "PUBLICATION"},
        )

        self.assertEqual(
            response.context["page_obj"].paginator.count,
            1,
        )

    def test_filter_by_activity_name_in_changes(self):
        self.login_admin()

        log = self.create_log(
            user=self.prof1,
            activity=self.activity2,
            action=self.action1,
            changes={"activity": "Projet confidentiel"},
            created_at=make_aware(
                datetime(2026, 4, 2, 12, 0),
                get_current_timezone()
            )
        )

        response = self.client.get(
            reverse("auditlogs"),
            {"activity": "confidentiel"},
        )

        self.assertIn(
            log.pk,
            self.get_all_logs(response).values_list("id", flat=True),
        )

    # ======================================================
    # Combined filters
    # ======================================================

    def test_multiple_filters_can_be_combined(self):
        self.login_admin()

        response = self.client.get(
            reverse("auditlogs"),
            {
                "date_from": "2026-01-01",
                "date_to": "2026-01-31",
                "performed_by": str(self.prof1.pk),
                "action": self.action1,
                "activity": "Publication",
            },
        )

        self.assertEqual(
            response.context["page_obj"].paginator.count,
            1,
        )

        self.assertEqual(
            list(self.get_logs(response)),
            [self.log1],
        )

    # ======================================================
    # Pagination
    # ======================================================

    def test_pagination_uses_configured_page_size(self):
        self.login_admin()

        response = self.client.get(reverse("auditlogs"))

        self.assertEqual(
            response.context["page_obj"].paginator.per_page,
            2,
        )

        self.assertEqual(
            len(response.context["page_obj"].object_list),
            2,
        )

        self.assertTrue(response.context["page_obj"].has_next())

    def test_can_access_second_page(self):
        self.login_admin()

        response = self.client.get(
            reverse("auditlogs"),
            {"page": "2"},
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            len(response.context["page_obj"].object_list),
            1,
        )

        self.assertFalse(response.context["page_obj"].has_next())

    def test_invalid_page_number_returns_first_page(self):
        self.login_admin()

        response = self.client.get(
            reverse("auditlogs"),
            {"page": "invalid"},
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.context["page_obj"].number,
            1,
        )

    def test_page_number_beyond_last_page_returns_last_page(self):
        self.login_admin()

        response = self.client.get(
            reverse("auditlogs"),
            {"page": "999"},
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.context["page_obj"].number,
            2,
        )

    def test_filters_are_applied_before_pagination(self):
        self.login_admin()

        response = self.client.get(
            reverse("auditlogs"),
            {
                "performed_by": str(self.prof1.pk),
                "page": "2",
            },
        )

        # Deux logs correspondent à prof1, donc une seule page
        # est nécessaire avec PAGINATION_LOGS=2.
        self.assertEqual(
            response.context["page_obj"].paginator.count,
            2,
        )

        self.assertEqual(
            response.context["page_obj"].number,
            1,
        )
