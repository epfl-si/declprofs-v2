from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from users.models import UserYear

User = get_user_model()


class CheckProfessorsCommandTest(TestCase):

    @patch("users.management.commands.check_professors.requests.get")
    def test_check_professors(self, mock_get):

        current_year = timezone.now().year

        members_response = Mock()
        members_response.json.return_value = {
            "members": [
                {
                    "type": "person",
                    "email": "john.doe@epfl.ch",
                    "id": "123456",
                    "username": "johndoe",
                    "first_name": "John",
                    "last_name": "Doe",
                },
            ]
        }
        members_response.raise_for_status.return_value = None

        accred_response = Mock()
        accred_response.json.return_value = {
            "accreds": [
                {
                    "person": {
                        "email": "john.doe@epfl.ch",
                        "firstname": "John",
                        "lastname": "Doe",
                    },
                    "order": 1,
                    "unit": {
                        "path": "ENAC",
                    },
                },
            ]
        }
        accred_response.raise_for_status.return_value = None

        mock_get.side_effect = [
            members_response,
            accred_response,
        ]

        call_command("check_professors")

        user = User.objects.get(sciper="123456")

        self.assertEqual(user.username, "johndoe")
        self.assertEqual(user.email, "john.doe@epfl.ch")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")
        self.assertEqual(user.unit, "ENAC")
        self.assertTrue(user.has_access)

        user_year = UserYear.objects.get(
            user=user,
            year=current_year,
        )

        self.assertTrue(user_year.is_employed)

        self.assertEqual(mock_get.call_count, 2)

    @patch("users.management.commands.check_professors.requests.get")
    def test_user_not_in_members_is_not_employed(self, mock_get):

        current_year = timezone.now().year

        user = User.objects.create_user(
            username="olduser",
            sciper="999999",
            email="olduser@epfl.ch",
            has_access=True,
        )

        UserYear.objects.create(
            user=user,
            year=current_year,
            is_employed=True,
        )

        members_response = Mock()
        members_response.json.return_value = {
            "members": []
        }
        members_response.raise_for_status.return_value = None

        mock_get.return_value = members_response

        call_command("check_professors")

        user_year = UserYear.objects.get(
            user=user,
            year=current_year,
        )

        self.assertFalse(user_year.is_employed)

    @patch("users.management.commands.check_professors.requests.get")
    def test_superuser_is_not_modified(self, mock_get):

        current_year = timezone.now().year

        user = User.objects.create_superuser(
            username="admin",
            sciper="999999",
            email="admin@epfl.ch",
        )

        UserYear.objects.create(
            user=user,
            year=current_year,
            is_employed=True,
        )

        members_response = Mock()
        members_response.json.return_value = {
            "members": []
        }
        members_response.raise_for_status.return_value = None

        mock_get.return_value = members_response

        call_command("check_professors")

        user_year = UserYear.objects.get(
            user=user,
            year=current_year,
        )

        self.assertTrue(user_year.is_employed)
