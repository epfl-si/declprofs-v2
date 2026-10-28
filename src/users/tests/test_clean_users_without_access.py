from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

User = get_user_model()


class CleanUsersWithoutAccessCommandTest(TestCase):

    def test_deletes_users_without_access(self):
        User.objects.create_user(
            username="user_without_access_1",
            sciper="123456",
            has_access=False,
        )

        User.objects.create_user(
            username="user_without_access_2",
            sciper="123457",
            has_access=False,
        )

        User.objects.create_user(
            username="user_with_access",
            sciper="654321",
            has_access=True,
        )

        output = StringIO()

        call_command(
            "clean_users_without_access",
            stdout=output,
        )

        self.assertEqual(User.objects.count(), 1)
        self.assertTrue(
            User.objects.filter(username="user_with_access").exists()
        )

        self.assertIn(
            "2 user(s) deleted.",
            output.getvalue(),
        )
