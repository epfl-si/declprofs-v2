import csv

from config.decorators import superuser_required
from datetime import date
from types import SimpleNamespace
from urllib.parse import urlencode
from weasyprint import HTML

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from .forms import ActivityForm
from .models import Activity
from auditlogs.models import ActivityLog
from campaigns.models import Campaign
from notifications.emails import send_submitted_notification, send_modified_by_apr
from users.models import UserYear

User = get_user_model()


####################################
#
# HOME
#
####################################

@login_required
def home(request):

    if request.user.is_superuser:
        activities = Activity.objects.select_related("user").all()
    else:
        activities = Activity.objects.filter(user=request.user)

    latest_campaign = Campaign.objects.order_by("-year").first()
    latest_year = latest_campaign.year if latest_campaign else None

    #
    # Filters
    #

    # Search user
    search_user = request.GET.get("professor", "").strip()

    if request.user.is_superuser and search_user:
        activities = activities.filter(
            user__sciper=search_user
        )

    # Search year
    year = request.GET.get("year", "").strip()

    if year.isdigit():
        year = int(year)

        if latest_year and year <= latest_year:
            activities = activities.filter(
                date_start__year__lte=year
            ).filter(
                Q(date_end__isnull=True)
                | Q(date_end__year__gte=year)
            )
        else:
            activities = activities.none()
    else:
        year = None

        if latest_year:
            activities = activities.filter(
                date_start__year__lte=latest_year
            )

    # Statistics for not admin users
    stats_user_count = {
        "activity_count": 0,
        "draft_count": 0,
        "submitted_count": 0,
        "missing_count": 0,    
    }

    if not request.user.is_superuser:

        stats_user_count["draft_count"] = activities.filter(
            status=Activity.ActivityStatusType.DRAFT
        ).count()

        stats_user_count["submitted_count"] = activities.filter(
            status=Activity.ActivityStatusType.SUBMITTED
        ).count()

        stats_user_count["activity_count"] = (
            stats_user_count["draft_count"]
            + stats_user_count["submitted_count"]
        )

        user_years = UserYear.objects.filter(user=request.user)

        if year:
            year = int(year)
            user_years = user_years.filter(year=year)

        stats_user_count["missing_count"] = sum(
            user_year.missing_count
            for user_year in user_years
        )

    # Pagination
    paginator = Paginator(activities.order_by("-date_start", "-id"), settings.PAGINATION_ACTIVITIES)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    activities = page_obj.object_list

    #
    # Form
    #

    activity = None

    activity_id = request.GET.get("id")

    if activity_id:

        activity = get_activity(request, activity_id)

        form = ActivityForm(instance=activity, current_user=request.user)

    else:

        initial = {}

        if request.user.is_superuser and search_user:

            selected_professor = User.objects.filter(sciper=search_user).first()

            if selected_professor:
                initial["user"] = selected_professor

        form = ActivityForm(current_user=request.user, initial=initial)

    if request.method == "POST":

        action = request.POST.get("action")

        if action == "create":

            form = ActivityForm(
                request.POST,
                current_user=request.user,
            )

            if form.is_valid():

                activity = form.save(commit=False)

                if not request.user.is_superuser:
                    activity.user = request.user

                user_years, message = check_eligibility(activity)

                if message:
                    form.add_error(None, message)
                    activity = None

                else:
                    activity.save()

                    ActivityLog.objects.create(
                        activity=activity,
                        user=request.user,
                        action=ActivityLog.Action.CREATED,
                        changes=activity.to_log_dict(),
                    )

                    for user_year in user_years:
                        user_year.add_draft_activity(save=True)

                    return redirect_to_home_with_params(request.user.is_superuser, activity.user.sciper, activity.pk, year)

        elif action == "duplicate":

            activity_id = request.POST.get("activity_id")

            activity = get_activity(request, activity_id)

            # Create a copy
            activity.pk = None
            activity.id = None

            # If a superuser duplicates, keep the owner
            # If an owner duplicates, assign himself
            if not request.user.is_superuser:
                activity.user = request.user

            # Reset dates for duplicated activity
            activity.date_start = timezone.now().date()
            activity.date_end = None

            user_years, message = check_eligibility(activity)

            if message:
                messages.error(request, message)
                return redirect(f"{reverse('home')}?id={activity_id}")

            activity.set_draft(save=False)
            activity.save()

            ActivityLog.objects.create(
                activity=activity,
                user=request.user,
                action=ActivityLog.Action.DUPLICATED,
                changes={
                    "user": str(activity.user),
                    "source": activity_id,
                },
            )

            for user_year in user_years:
                user_year.add_draft_activity(save=True)

            return redirect_to_home_with_params(request.user.is_superuser, activity.user.sciper, activity.pk, year)

        elif action == "save":

            activity_id = request.POST.get("activity_id")
            activity = get_activity(request, activity_id)

            old_activity = SimpleNamespace(
                years=activity.get_years(),
                user=activity.user,
                status=activity.status,
                is_draft=activity.is_draft,
                is_submitted=activity.is_submitted,
            )

            old_values = activity.to_log_dict()

            form = ActivityForm(
                request.POST,
                instance=activity,
                current_user=request.user,
            )

            if form.is_valid():

                updated_activity = form.save(commit=False)

                # Ensure non-admin users cannot change the activity owner
                if not request.user.is_superuser:
                    updated_activity.user = request.user

                user_years, message = check_update_eligibility(updated_activity)
                
                if message:
                    form.add_error(None, message)
                else:
                    update_activity_counters(old_activity, updated_activity)
                    updated_activity.save()

                    changes = updated_activity.get_changes(old_values)

                    if changes:
                        ActivityLog.objects.create(
                            activity=updated_activity,
                            user=request.user,
                            action=ActivityLog.Action.UPDATED,
                            changes=changes,
                        )

                    if request.user.is_superuser:
                        send_modified_by_apr(
                            {
                                "name": updated_activity.user.get_full_name(),
                                "to": updated_activity.user.email,
                                "cc": settings.DEFAULT_FROM_EMAIL,
                                "date": timezone.now().date(),
                            },
                        )

                    return redirect_to_home_with_params(request.user.is_superuser, updated_activity.user.sciper, updated_activity.pk, year, request.POST.get("page"),)

        elif action == "submit_drafts":

            if request.user.is_superuser:
                search_professor = request.POST.get("professor")
                if search_professor:
                    current_user = get_object_or_404(
                        User,
                        sciper=search_professor
                    )
                else:
                    messages.error(request, "Please select a professor.")
                                   
                    return redirect("home")
            else:
                current_user = request.user

            drafts = Activity.objects.filter(
                user=current_user,
                status=Activity.ActivityStatusType.DRAFT,
            )

            year_submit = year if year else timezone.now().year

            year_start = date(year_submit, 1, 1)
            year_end = date(year_submit, 12, 31)

            drafts = drafts.filter(
                date_start__lte=year_end,
            ).filter(
                Q(date_end__gte=year_start) | Q(date_end__isnull=True)
            )

            if not drafts.exists():
                messages.warning(request, f"There are no draft activities to submit for {year_submit}.")
                
                return redirect(f"{reverse('home')}?{urlencode({ "professor": current_user.sciper })}")
            
            return render(
                request,
                "activities/confirm_submission.html",
                {
                    "current_user": current_user,
                    "drafts_count": drafts.count(),
                    "year": year_submit,
                },
            )

        elif action == "confirm_submit_drafts":

            if request.user.is_superuser:
                search_professor = request.GET.get("professor")

                if search_professor:
                    current_user = get_object_or_404(
                        User,
                        sciper=search_professor,
                    )
                else:
                    messages.warning(
                        request,
                        "Please select a professor."
                    )
                    return redirect("home")
            else:
                current_user = request.user

            drafts = Activity.objects.filter(
                user=current_user,
                status=Activity.ActivityStatusType.DRAFT,
            )

            year_submit = year if year else timezone.now().year
            
            year_start = date(year_submit, 1, 1)
            year_end = date(year_submit, 12, 31)

            drafts = drafts.filter(
                date_start__lte=year_end,
            ).filter(
                Q(date_end__gte=year_start) | Q(date_end__isnull=True)
            )

            for activity in drafts:
                activity.set_submitted()

                ActivityLog.objects.create(
                    activity=activity,
                    user=request.user,
                    action=ActivityLog.Action.SUBMITTED,
                    changes={
                        "user": str(activity.user),
                        "status": {
                            "old": Activity.ActivityStatusType.DRAFT,
                            "new": Activity.ActivityStatusType.SUBMITTED,
                        },
                    },
                )

                years = activity.get_years()

                user_years, _ = get_user_year_eligibility(
                    activity.user,
                    years,
                )

                # Accepts years that are no longer eligible because the record
                # was created before the eligibility rules changed.
                # In such cases, the user can submit during later periods.
                for user_year in user_years:
                    user_year.promote_activity(save=True)

            send_submitted_notification(
                {
                    "name": current_user.get_full_name(),
                    "date": timezone.now().date(),
                    "cc": current_user.email,
                },
            )

            return redirect_to_home_with_params(request.user.is_superuser, current_user.sciper, None, year)

        elif action == "delete":

            activity_id = request.POST.get("activity_id")
            activity = get_activity(request, activity_id)

            user_years, message = check_eligibility(activity)

            if message:
                messages.error(request, message)

                params = {}
                if request.user.is_superuser:
                    params["professor"] = activity.user.sciper
                params["year"] = request.POST.get("year") or year
                params["id"] = activity.id
                params["page"] = request.POST.get("page")

                params = {k: v for k, v in params.items() if v not in (None, "")}

                return redirect(f"{reverse('home')}?{urlencode(params)}")

            current_user = activity.user

            ActivityLog.objects.create(
                activity=activity,
                user=request.user,
                action=ActivityLog.Action.DELETED,
                changes=activity.to_log_dict(),
            )

            for user_year in user_years:
                user_year.remove_activity(activity, save=True)
            activity.delete()

            return redirect_to_home_with_params(request.user.is_superuser, current_user.sciper, None, year)

    # For filter fields
    users = []
    if request.user.is_superuser:
        users = User.objects.order_by("last_name", "first_name")

    return render(
        request,
        "activities/home.html",
        {
            "activities": activities,
            "page_obj": page_obj,
            "selected_activity": activity,
            "form": form,
            "search_user": search_user,
            "year": request.GET.get("year", ""),
            "professors": users,
            "stats_user_count": stats_user_count,
        },
    )


def get_activity(request, activity_id):
    if request.user.is_superuser:
        return get_object_or_404(Activity, pk=activity_id)

    return get_object_or_404(
        Activity,
        pk=activity_id,
        user=request.user,
    )


def redirect_to_home_with_params(is_superuser, sciper, activity_id, year, page=None):
    params = {}
    if is_superuser:
        params["professor"] = sciper
    if year:
        params["year"] = year
    if activity_id:
        params["id"] = activity_id
    if page:
        params["page"] = page
    params = { k: v for k, v in params.items() if v }

    return redirect(f"{reverse('home')}?{urlencode(params)}")


def format_ineligible_message(ineligible_years):
    if len(ineligible_years) > 1:
        return (
            f"The campaign years "
            f"{', '.join(map(str, ineligible_years))} are closed"
        )

    return f"The campaign {ineligible_years[0]} is closed"


def check_eligibility(activity):
    """
    Check that all campaign years covered by an activity
    are eligible.

    Used when creating a new activity or duplicating
    an existing one.
    """

    years = activity.get_years()

    user_years, ineligible_years = get_user_year_eligibility(
        activity.user,
        years,
    )

    if ineligible_years:
        return user_years, format_ineligible_message(ineligible_years)

    return user_years, None


def check_update_eligibility(activity):
    """
    Check if an existing activity can still be modified.

    An update is allowed if:
    - all covered years are eligible, or
    - the activity is still ongoing in the current year.
    """

    years = activity.get_years()

    user_years, ineligible_years = get_user_year_eligibility(
        activity.user,
        years,
    )

    # Everything is still eligible
    if not ineligible_years:
        return user_years, None

    return user_years, format_ineligible_message(ineligible_years)


def get_user_year_eligibility(user, years):

    user_years = list(
        UserYear.objects.filter(
            user=user,
            year__in=years,
            is_eligible=True,
        )
    )

    eligible_years = { user_year.year for user_year in user_years }

    ineligible_years = sorted(years - eligible_years)

    return user_years, ineligible_years


def update_activity_counters(old_activity, new_activity):
    """
    Synchronize UserYear counters after activity update.
    """

    old_years = old_activity.years
    new_years = new_activity.get_years()

    old_user = old_activity.user
    new_user = new_activity.user

    years_changed = old_years != new_years
    user_changed = old_user != new_user
    status_changed = old_activity.status != new_activity.status

    if not (years_changed or user_changed or status_changed):
        return

    # Remove previous state
    for year in old_years:
        user_year = UserYear.objects.get(
            user=old_user,
            year=year,
        )
        user_year.remove_activity(
            old_activity,
            save=True,
        )

    # Add new state
    for year in new_years:
        user_year = UserYear.objects.filter(
            user=new_user,
            year=year,
        ).first()

        if not user_year:
            continue

        if old_activity.is_draft:
            user_year.add_draft_activity(save=True)

        elif old_activity.is_submitted:
            user_year.add_submitted_activity(save=True)


####################################
#
# REPORTING
#
####################################

@superuser_required
def disclosure_report(request):

    if not request.user.is_superuser:
        return HttpResponse(status=403)

    professor = request.GET.get("professor")
    year = request.GET.get("year")

    if not professor or not year:
        messages.error(request, "Please select a professor and a year.")
        return redirect("home")

    professor = get_object_or_404(User, sciper=professor)

    activities = (
        Activity.objects
        .filter(user=professor)
        .filter(date_start__year__lte=year)
        .filter(
            Q(date_end__isnull=True) |
            Q(date_end__year__gte=year)
        )
        .order_by("date_start")
    )

    html = render_to_string(
        "activities/report.html",
        {
            "professor": professor,
            "year": year,
            "activities": activities,
        },
    )

    pdf = HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="{professor.sciper}-{year}.pdf"'
    )
    return response


@superuser_required
def report_csv(request):

    professor_id = request.GET.get("professor")
    year = request.GET.get("year")

    if not year:
        messages.error(request, "Please select a year.")
        return redirect("home")

    activities = (
        Activity.objects
        .filter(date_start__year__lte=year)
        .filter(
            Q(date_end__isnull=True) |
            Q(date_end__year__gte=year)
        )
    )

    professor = None

    if professor_id:
        professor = get_object_or_404(User, sciper=professor_id)
        activities = activities.filter(user=professor)

    activities = activities.order_by("date_start")


    response = HttpResponse(
        content_type="text/csv; charset=utf-8"
    )

    response.write("\ufeff")

    filename = (
        f"{professor.sciper}-{year}.csv"
        if professor
        else f"all-professors-{year}.csv"
    )

    response["Content-Disposition"] = (
        f'attachment; filename="{filename}"'
    )

    writer = csv.writer(response)

    writer.writerow([
        "Professor",
        "Email",
        "Sciper",
        "Unit",
        "Year",
        "Activity",
        "Principal",
        "Comments",
        "APR comments",
        "Start date",
        "End date",
        "Status",
    ])

    for activity in activities:
        writer.writerow([
            activity.user.get_full_name(),
            activity.user.email,
            activity.user.sciper,
            activity.user.unit,
            year,
            activity.activity,
            activity.principal,
            activity.comments,
            activity.comments_apr,
            activity.date_start.strftime("%d/%m/%Y"),
            activity.date_end.strftime("%d/%m/%Y")
            if activity.date_end else "",
            activity.status,
        ])

    return response
