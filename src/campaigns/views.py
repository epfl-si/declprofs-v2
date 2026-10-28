from collections import defaultdict
from config.decorators import superuser_required

from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone

from .forms import CampaignForm
from .models import Campaign
from .services import update_user_years_for_campaign
from users.models import UserYear

User = get_user_model()


@superuser_required
def home(request):
    # Filters GET
    selected_professor = request.GET.get("professor")
    selected_year = request.GET.get("year")
    campaign_year = request.GET.get("campaign_year")

    # Users
    users_qs = User.objects.order_by("last_name", "first_name")

    if request.user.is_superuser and selected_professor:
        users_qs = users_qs.filter(sciper=selected_professor)

    if selected_year:
        years = [int(selected_year)]
    else:
        years = list(
            Campaign.objects.order_by("-year").values_list("year", flat=True)
        )

    # Selected campaign
    campaign = None

    if campaign_year:
        try:
            campaign_year = int(campaign_year)
        except ValueError:
            campaign_year = None

    if campaign_year:
        campaign = Campaign.objects.filter(year=campaign_year).first()

    if campaign_year is None:
        campaign = Campaign.objects.first()

    if request.method == "POST":

        # Save campaign
        if "save_campaign" in request.POST:

            campaign_year = request.POST.get("year")

            try:
                campaign_year = int(campaign_year)
            except (TypeError, ValueError):
                campaign_year = None

            if campaign_year:
                campaign = Campaign.objects.filter(year=campaign_year).first()
            else:
               campaign = None

            form = CampaignForm(request.POST, instance=campaign)

            if form.is_valid():
                campaign = form.save()

                update_user_years_for_campaign(campaign)

                return redirect(f"/campaign/?campaign_year={campaign.year}")

        # Save manual eligibilities
        elif "save_eligibility" in request.POST:

            visible_user_years = UserYear.objects.filter(
                user__in=users_qs,
                year__in=years,
            )

            checked_ids = [
                int(key.split("_")[1])
                for key in request.POST
                if key.startswith("eligible_")
            ]

            visible_user_years.filter(
                id__in=checked_ids
            ).update(
                is_eligible=True
            )

            visible_user_years.exclude(
                id__in=checked_ids
            ).update(
                is_eligible=False
            )

            return redirect("campaign")

    else:
        if campaign:
            form = CampaignForm(instance=campaign)
        elif campaign_year:
            # New year: prefill only with year field.
            form = CampaignForm(initial={"year": campaign_year})
        else:
            form = CampaignForm(instance=campaign)

    # Table
    user_years = UserYear.objects.select_related("user").filter(
        user__in=users_qs,
        year__in=years,
    )

    eligibility = defaultdict(dict)

    for uy in user_years:
        eligibility[uy.user_id][uy.year] = uy

    rows = []

    for user in users_qs:
        rows.append(
            {
                "user": user,
                "years": [
                    eligibility[user.id].get(year)
                    for year in years
                ],
            }
        )

    professors = []

    if request.user.is_superuser:
        professors = User.objects.order_by(
            "last_name",
            "first_name",
        )

    campaign_years = list(
        Campaign.objects
        .order_by("-year")
        .values_list("year", flat=True)
    )

    return render(
        request,
        "campaigns/home.html",
        {
            "form": form,
            "campaign": campaign,
            "campaign_years": campaign_years,
            "years": years,
            "rows": rows,
            "professors": professors,
        },
    )


@superuser_required
def campaign_by_year(request):
    year = request.GET.get("year")

    try:
        year = int(year)
    except (TypeError, ValueError):
        return JsonResponse({"exists": False})

    campaign = Campaign.objects.filter(year=year).first()

    if campaign is None:
        return JsonResponse({
            "exists": False,
            "year": year,
        })

    return JsonResponse({
        "exists": True,
        "year": campaign.year,
        "opening_date": timezone.localtime(campaign.opening_date).strftime("%Y-%m-%dT%H:%M:%S"),
        "closing_date": timezone.localtime(campaign.closing_date).strftime("%Y-%m-%dT%H:%M:%S"),
        "is_open": campaign.is_open,
    })
