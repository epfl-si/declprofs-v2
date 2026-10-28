from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from documentation.models import Documentation

User = get_user_model()


class DocumentationHomeViewTest(TestCase):

    def setUp(self):
        # --------------------------------------------------
        # Users
        # --------------------------------------------------

        self.admin = User.objects.create_superuser(
            username="admin",
            password="password",
            sciper="999999",
            has_access=True,
        )

        self.user = User.objects.create_user(
            username="user",
            password="password",
            sciper="111111",
            has_access=True,
        )

        # --------------------------------------------------
        # Documentation USER
        # --------------------------------------------------

        self.user_doc_2 = Documentation.objects.create(
            type=Documentation.Type.USER,
            order=2,
        )

        self.user_doc_1 = Documentation.objects.create(
            type=Documentation.Type.USER,
            order=1,
        )

        # --------------------------------------------------
        # Documentation BUSINESS
        # --------------------------------------------------

        self.business_doc_2 = Documentation.objects.create(
            type=Documentation.Type.BUSINESS,
            order=2,
        )

        self.business_doc_1 = Documentation.objects.create(
            type=Documentation.Type.BUSINESS,
            order=1,
        )

    # ======================================================
    # Helpers
    # ======================================================

    def login_admin(self):
        self.client.force_login(self.admin)

    def login_user(self):
        self.client.force_login(self.user)

    # ======================================================
    # Access
    # ======================================================

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse("documentation"))

        self.assertEqual(response.status_code, 302)

    def test_regular_user_can_access_home(self):
        self.login_user()

        response = self.client.get(reverse("documentation"))

        self.assertEqual(response.status_code, 200)

    def test_superuser_can_access_home(self):
        self.login_admin()

        response = self.client.get(reverse("documentation"))

        self.assertEqual(response.status_code, 200)

    # ======================================================
    # Template and context
    # ======================================================

    def test_home_uses_correct_template(self):
        self.login_user()

        response = self.client.get(reverse("documentation"))

        self.assertTemplateUsed(
            response,
            "documentation/home.html",
        )

    def test_home_returns_expected_context(self):
        self.login_user()

        response = self.client.get(reverse("documentation"))

        self.assertIn("documentation_user", response.context)
        self.assertIn("documentation_business", response.context)

    # ======================================================
    # Regular user
    # ======================================================

    def test_regular_user_sees_user_documentation(self):
        self.login_user()

        response = self.client.get(reverse("documentation"))

        documentation = list(
            response.context["documentation_user"]
        )

        self.assertEqual(
            documentation,
            [self.user_doc_1, self.user_doc_2],
        )

    def test_regular_user_does_not_see_business_documentation(self):
        self.login_user()

        response = self.client.get(reverse("documentation"))

        self.assertFalse(
            response.context["documentation_business"].exists()
        )

    # ======================================================
    # Superuser
    # ======================================================

    def test_superuser_sees_user_documentation(self):
        self.login_admin()

        response = self.client.get(reverse("documentation"))

        documentation = list(
            response.context["documentation_user"]
        )

        self.assertEqual(
            documentation,
            [self.user_doc_1, self.user_doc_2],
        )

    def test_superuser_sees_business_documentation(self):
        self.login_admin()

        response = self.client.get(reverse("documentation"))

        documentation = list(
            response.context["documentation_business"]
        )

        self.assertEqual(
            documentation,
            [self.business_doc_1, self.business_doc_2],
        )

    # ======================================================
    # Ordering
    # ======================================================

    def test_user_documentation_is_ordered_by_order(self):
        self.login_user()

        response = self.client.get(reverse("documentation"))

        documentation = list(
            response.context["documentation_user"]
        )

        orders = [doc.order for doc in documentation]

        self.assertEqual(orders, sorted(orders))

    def test_business_documentation_is_ordered_by_order(self):
        self.login_admin()

        response = self.client.get(reverse("documentation"))

        documentation = list(
            response.context["documentation_business"]
        )

        orders = [doc.order for doc in documentation]

        self.assertEqual(orders, sorted(orders))

    # ======================================================
    # Separation of documentation types
    # ======================================================

    def test_user_documentation_contains_only_user_type(self):
        self.login_admin()

        response = self.client.get(reverse("documentation"))

        for doc in response.context["documentation_user"]:
            self.assertEqual(
                doc.type,
                Documentation.Type.USER,
            )

    def test_business_documentation_contains_only_business_type(self):
        self.login_admin()

        response = self.client.get(reverse("documentation"))

        for doc in response.context["documentation_business"]:
            self.assertEqual(
                doc.type,
                Documentation.Type.BUSINESS,
            )
