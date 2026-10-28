from config.decorators import superuser_required

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import NotificationFormSet
from .models import Notification
from campaigns.models import Campaign
from notifications.emails import send_reminders
from users.models import UserYear

User = get_user_model()


@superuser_required
def home(request):

    queryset = Notification.objects.order_by("name")

    if request.method == "POST":

        formset = NotificationFormSet(request.POST, queryset=queryset)

        if formset.is_valid():
            formset.save()

            return redirect("notifications")

    else:

        formset = NotificationFormSet(queryset=queryset)

    return render(
        request,
        "notifications/home.html",
        {
            "formset": formset,
        },
    )


@superuser_required
def reminders(request):
    year = timezone.now().year

    campaign = Campaign.objects.filter(year=year).first()

    if not campaign:

        messages.error(request, f"The campaign {year} doesn't exist")

        return render(
            request,
            "notifications/reminders.html",
            {
                "user_years": [],
            },
        )

    user_years = (
        UserYear.objects
        .select_related("user")
        .filter(year=campaign.year, is_employed=True)
    )

    # Filter professor
    search_user = request.GET.get("professor", "").strip()

    if search_user:
        user_years = user_years.filter(
            user__sciper=search_user
        )

    user_years = user_years.order_by(
        "user__last_name",
        "user__first_name",
    )

    if request.method == "POST":

        now = timezone.localtime()

        selected_ids = request.POST.getlist("send_reminder")

        if not selected_ids:
            return redirect("reminders")

        user_years_to_remind = UserYear.objects.select_related(
            "user"
        ).filter(
            id__in=selected_ids,
            year=campaign.year,
        )

        bcc = []

        for user_year in user_years_to_remind:

            if not user_year.user.email:
                continue

            bcc.append(user_year.user.email)

            user_year.reminder_at = now
            user_year.save(update_fields=["reminder_at"])

        context = {
            "year": campaign.year,
            "bcc": ",".join(bcc),
        }

        send_reminders(context)

        return redirect("reminders")

    # For filter user field
    users = []
    if request.user.is_superuser:
        users = User.objects.order_by("last_name", "first_name")

    if campaign.is_open:
        messages.success(request, f"The campaign {year} is opened")
    else:
        messages.info(request, f"The campaign {year} is closed")

    return render(
        request,
        "notifications/reminders.html",
        {
            "user_years": user_years,
            "professors": users,
        },
    )
