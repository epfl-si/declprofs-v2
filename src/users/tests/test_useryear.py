from types import SimpleNamespace

from django.test import TestCase
from django.contrib.auth import get_user_model

from users.models import UserYear

User = get_user_model()


class UserYearTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="prof1",
            sciper="123456",
            password="test",
        )

        self.user_year = UserYear.objects.create(
            user=self.user,
            year=2026,
            is_eligible=True,
        )

    def test_initial_counters(self):

        self.assertEqual(
            self.user_year.draft_count,
            0,
        )

        self.assertEqual(
            self.user_year.submitted_count,
            0,
        )

        self.assertEqual(
            self.user_year.missing_count,
            1,
        )

    def test_add_draft_activity(self):

        self.user_year.add_draft_activity()

        self.user_year.refresh_from_db()

        self.assertEqual(
            self.user_year.draft_count,
            1,
        )

        self.assertEqual(
            self.user_year.missing_count,
            0,
        )

    def test_promote_activity(self):

        self.user_year.draft_count = 2
        self.user_year.save()

        self.user_year.promote_activity()

        self.user_year.refresh_from_db()

        self.assertEqual(
            self.user_year.draft_count,
            1,
        )

        self.assertEqual(
            self.user_year.submitted_count,
            1,
        )

    def test_remove_last_draft_activity(self):

        self.user_year.draft_count = 1
        self.user_year.missing_count = 0
        self.user_year.save()

        activity = SimpleNamespace(
            is_draft=True,
            is_submitted=False,
        )

        self.user_year.remove_activity(activity)

        self.user_year.refresh_from_db()

        self.assertEqual(
            self.user_year.draft_count,
            0,
        )

        self.assertEqual(
            self.user_year.missing_count,
            1,
        )

    def test_activity_lifecycle(self):

        # create
        self.user_year.add_draft_activity()

        self.user_year.refresh_from_db()

        self.assertEqual(
            self.user_year.draft_count,
            1,
        )

        # submit
        self.user_year.promote_activity()

        self.user_year.refresh_from_db()

        self.assertEqual(
            self.user_year.draft_count,
            0,
        )

        self.assertEqual(
            self.user_year.submitted_count,
            1,
        )

    def test_is_complete_when_all_conditions_are_met(self):

        self.user_year.submitted_count = 1
        self.user_year.draft_count = 0
        self.user_year.missing_count = 0
        self.user_year.save()

        self.assertTrue(
            self.user_year.is_complete,
        )

    def test_is_not_complete_when_there_are_drafts(self):

        self.user_year.submitted_count = 1
        self.user_year.draft_count = 1
        self.user_year.missing_count = 0
        self.user_year.save()

        self.assertFalse(
            self.user_year.is_complete,
        )

    def test_is_not_complete_when_there_are_missing_activities(self):

        self.user_year.submitted_count = 1
        self.user_year.draft_count = 0
        self.user_year.missing_count = 1
        self.user_year.save()

        self.assertFalse(
            self.user_year.is_complete,
        )

    def test_is_not_complete_when_nothing_is_submitted(self):

        self.user_year.submitted_count = 0
        self.user_year.draft_count = 0
        self.user_year.missing_count = 1
        self.user_year.save()

        self.assertFalse(
            self.user_year.is_complete,
        )

    def test_add_submitted_activity(self):

        self.user_year.add_submitted_activity(save=False)

        self.assertEqual(
            self.user_year.submitted_count,
            1,
        )

        self.assertEqual(
            self.user_year.missing_count,
            0,
        )

        user_year_from_db = UserYear.objects.get(
            pk=self.user_year.pk,
        )

        self.assertEqual(
            user_year_from_db.submitted_count,
            0,
        )

        self.assertEqual(
            user_year_from_db.missing_count,
            1,
        )

        self.user_year.refresh_from_db()

        self.user_year.add_submitted_activity()

        user_year_from_db = UserYear.objects.get(
            pk=self.user_year.pk,
        )

        self.assertEqual(
            user_year_from_db.submitted_count,
            1,
        )

        self.assertEqual(
            user_year_from_db.missing_count,
            0,
        )
