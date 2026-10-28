from config.decorators import superuser_required

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase

User = get_user_model()


class SuperuserRequiredDecoratorTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

        self.user = User.objects.create_user(
            username="prof",
            sciper="111111",
            password="password",
        )

        self.admin = User.objects.create_superuser(
            username="admin",
            sciper="999999",
            password="password",
        )

    def test_superuser_can_access_view(self):

        request = self.factory.get("/")

        request.user = self.admin

        view_called = False

        def my_view(request):
            nonlocal view_called
            view_called = True
            return "ok"

        decorated_view = superuser_required(my_view)

        response = decorated_view(request)

        self.assertTrue(view_called)

        self.assertEqual(
            response,
            "ok",
        )

    def test_authenticated_non_superuser_is_rejected(self):

        request = self.factory.get("/")

        request.user = self.user

        decorated_view = superuser_required(
            lambda request: "ok"
        )

        with self.assertRaises(PermissionDenied):
            decorated_view(request)

    def test_anonymous_user_is_rejected(self):

        request = self.factory.get("/")

        request.user = AnonymousUser()

        decorated_view = superuser_required(
            lambda request: "ok"
        )

        with self.assertRaises(PermissionDenied):
            decorated_view(request)