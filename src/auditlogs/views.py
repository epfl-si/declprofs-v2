from config.decorators import superuser_required
from datetime import datetime, time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone

from .models import ActivityLog, EmailLog

User = get_user_model()


@superuser_required
def home(request):

    logs = (ActivityLog.objects.select_related("user", "activity", "activity__user"))

    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------

    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()
    performed_by = request.GET.get("performed_by", "").strip()
    owner = request.GET.get("owner", "").strip()
    action = request.GET.get("action", "").strip()
    activity_search = request.GET.get("activity", "").strip()

    # Date from
    if date_from:
        try:
            value = datetime.strptime(date_from, "%Y-%m-%d").date()

            start_datetime = timezone.make_aware(
                datetime.combine(value, time.min)
            )

            logs = logs.filter(created_at__gte=start_datetime)

        except ValueError:
            date_from = ""

    # Date to
    if date_to:
        try:
            value = datetime.strptime(date_to, "%Y-%m-%d").date()

            end_datetime = timezone.make_aware(
                datetime.combine(value, time.max)
            )

            logs = logs.filter(created_at__lte=end_datetime)

        except ValueError:
            date_to = ""

    # Performed by
    if performed_by:
        logs = logs.filter(user_id=performed_by)

    # Owner
    if owner:
        logs = logs.filter(Q(activity__user_id=owner) | Q(changes__user_id=owner))

    # Action
    if action:
        logs = logs.filter(action=action)

    # Activity
    if activity_search:
        logs = logs.filter(
            Q(activity__activity__icontains=activity_search)
            | Q(changes__activity__icontains=activity_search)
        )

    # ------------------------------------------------------------------
    # Pagination
    # ------------------------------------------------------------------

    paginator = Paginator(logs, settings.PAGINATION_LOGS)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    users = User.objects.order_by("last_name", "first_name")

    return render(
        request,
        "auditlogs/home.html",
        {
            "page_obj": page_obj,
            "users": users,
            "date_from": date_from,
            "date_to": date_to,
            "performed_by": performed_by,
            "owner": owner,
            "action": action,
            "activity_search": activity_search,
            "action_choices": ActivityLog.Action.choices,
        },
    )


@superuser_required
def email_logs(request):

    logs = EmailLog.objects.all()

    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------

    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()
    status = request.GET.get("status", "").strip()
    notification_type = request.GET.get("notification_type", "").strip()
    search = request.GET.get("search", "").strip()

    # Date from
    if date_from:
        try:
            value = datetime.strptime(
                date_from, "%Y-%m-%d"
            ).date()

            start_datetime = timezone.make_aware(
                datetime.combine(value, time.min)
            )

            logs = logs.filter(
                created_at__gte=start_datetime
            )

        except ValueError:
            date_from = ""

    # Date to
    if date_to:
        try:
            value = datetime.strptime(
                date_to, "%Y-%m-%d"
            ).date()

            end_datetime = timezone.make_aware(
                datetime.combine(value, time.max)
            )

            logs = logs.filter(
                created_at__lte=end_datetime
            )

        except ValueError:
            date_to = ""

    # Status
    if status:
        logs = logs.filter(status=status)

    # Notification type
    if notification_type:
        logs = logs.filter(
            notification_type=notification_type
        )

    # Search by subject or notification type
    if search:
        logs = logs.filter(
            Q(subject__icontains=search)
            | Q(notification_type__icontains=search)
        )

    paginator = Paginator(
        logs,
        settings.PAGINATION_LOGS,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    # Types de notifications effectivement enregistrés
    notification_types = (
        EmailLog.objects
        .order_by("notification_type")
        .values_list("notification_type", flat=True)
        .distinct()
    )

    return render(
        request,
        "auditlogs/email_logs.html",
        {
            "page_obj": page_obj,
            "date_from": date_from,
            "date_to": date_to,
            "status": status,
            "notification_type": notification_type,
            "search": search,
            "status_choices": EmailLog.Status.choices,
            "notification_types": notification_types,
        },
    )
