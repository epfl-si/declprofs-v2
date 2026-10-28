from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from activities.models import Activity

User = get_user_model()


class ActivityModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="prof",
            sciper="123456",
            password="password",
        )

    def test_clean_raises_validation_error_when_end_before_start(self):

        activity = Activity(
            user=self.user,
            activity="Teaching",
            principal="EPFL",
            date_start="2026-02-01",
            date_end="2026-01-01",
        )

        with self.assertRaises(ValidationError) as context:
            activity.clean()

        self.assertEqual(
            context.exception.message_dict,
            {
                "date_end": [
                    "End date must be greater or equal than start date."
                ]
            },
        )

    def test_str(self):

        activity = Activity.objects.create(
            user=self.user,
            activity="Teaching",
            principal="EPFL",
            date_start="2026-01-01",
        )

        self.assertEqual(
            str(activity),
            "Teaching - EPFL",
        )

    def test_set_draft_saves_status(self):

        activity = Activity.objects.create(
            user=self.user,
            activity="Teaching",
            principal="EPFL",
            date_start="2026-01-01",
            status=Activity.ActivityStatusType.SUBMITTED,
        )

        activity.set_draft()

        activity.refresh_from_db()

        self.assertEqual(
            activity.status,
            Activity.ActivityStatusType.DRAFT,
        )

        self.assertTrue(
            activity.is_draft,
        )

    def test_set_submitted_saves_status(self):

        activity = Activity.objects.create(
            user=self.user,
            activity="Teaching",
            principal="EPFL",
            date_start="2026-01-01",
        )

        activity.set_submitted()

        activity.refresh_from_db()

        self.assertEqual(
            activity.status,
            Activity.ActivityStatusType.SUBMITTED,
        )

        self.assertTrue(
            activity.is_submitted,
        )
