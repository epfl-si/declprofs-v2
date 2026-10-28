from django.shortcuts import redirect
from django.urls import reverse


class UserAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and not request.user.has_access
            and not request.user.is_superuser
            and request.path != reverse("forbidden")
        ):
            return redirect("forbidden")

        return self.get_response(request)
