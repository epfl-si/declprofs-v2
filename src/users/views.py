from config.decorators import superuser_required

from django.db.models import Count, Q
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model

from .models import UserYear

User = get_user_model()


@superuser_required
def home(request):

    selected_year = request.GET.get("year")
    selected_exempted = request.GET.get("exempted")
    selected_professor = request.GET.get("professor")
    selected_status = request.GET.get("status")

    # Get all years available in UserYear
    years = list(
        UserYear.objects.order_by("-year")
        .values_list("year", flat=True)
        .distinct()
    )

    # Selected year by default
    if not selected_year and years:
        selected_year = str(years[0])

    if request.method == "POST":

        user_year_ids = request.POST.getlist("user_year_ids")

        user_years_to_update = UserYear.objects.filter(id__in=user_year_ids)

        for user_year in user_years_to_update:

            user_year.is_exempted = (
                f"exempted_{user_year.id}" in request.POST
            )

            user_year.is_eligible = (
                f"eligible_{user_year.id}" in request.POST and not user_year.is_exempted
            )

        UserYear.objects.bulk_update(
            user_years_to_update,
            [
                "is_eligible",
                "is_exempted",
            ],
        )

        return redirect(request.get_full_path())

    # UserYear
    user_years = UserYear.objects.select_related(
        "user"
    ).filter(
        year=selected_year, is_employed=True
    ).order_by(
        "user__last_name",
        "user__first_name",
    )

    # Filter: professeur
    if selected_professor:
        user_years = user_years.filter(
            user__sciper=selected_professor
        )

    # Filter: exempted
    if selected_exempted:
        user_years = user_years.filter(
            is_exempted=True
        )

    # Compute stats before filtering by status
    stats = user_years.aggregate(
            total=Count("id"),
            submitted=Count(
                "id",
                filter=Q(
                    submitted_count__gt=0,
                    draft_count=0,
                    missing_count=0,
                ),
            ),
            incomplete=Count(
                "id",
                filter=Q(
                    draft_count__gt=0,
                ),
            ),
            missings=Count(
                "id",
                filter=Q(
                    missing_count__gt=0,
                ),
            ),
        )

    # Filter: statuses
    if selected_status == "submitted":
        user_years = user_years.filter(
            submitted_count__gt=0,
            draft_count=0,
            missing_count=0,
        )
    elif selected_status == "incomplete":
        user_years = user_years.filter(
            draft_count__gt=0,
        )
    elif selected_status == "missing":
        user_years = user_years.filter(
            missing_count__gt=0,
        )

    # Get all professors
    professors = User.objects.order_by(
        "last_name",
        "first_name",
    )

    year = int(selected_year) if selected_year else None

    for user_year in user_years:
        user_year.apr_comments = []

        if year:
            seen_comments = set()

            for activity in user_year.user.activities.all():
                if (
                    year in activity.get_years()
                    and activity.comments_apr.strip()
                ):
                    comment = activity.comments_apr.strip()

                    if comment not in seen_comments:
                        seen_comments.add(comment)
                        user_year.apr_comments.append(comment)

    return render(
        request,
        "users/home.html",
        {
            "user_years": user_years,
            "years": years,
            "selected_year": selected_year,
            "professors": professors,
            "stats": stats,
            "selected_status": selected_status,
        },
    )
