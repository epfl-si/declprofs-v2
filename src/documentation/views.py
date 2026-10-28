from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Documentation


@login_required
def home(request):

    if request.user.is_superuser:
        documentation_user = Documentation.objects.filter(
            type=Documentation.Type.USER
        ).order_by("order")

        documentation_business = Documentation.objects.filter(
            type=Documentation.Type.BUSINESS
        ).order_by("order")

    else:
        documentation_user = Documentation.objects.filter(
            type=Documentation.Type.USER
        ).order_by("order")

        documentation_business = Documentation.objects.none()

    return render(
        request,
        "documentation/home.html",
        {
            "documentation_user": documentation_user,
            "documentation_business": documentation_business,
        },
    )
