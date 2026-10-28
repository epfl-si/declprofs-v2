from django.contrib.auth import get_user_model

from users.models import UserYear

User = get_user_model()


def update_user_years_for_campaign(campaign):

    users = User.objects.all()

    existing = {
        uy.user_id: uy
        for uy in UserYear.objects.filter(
            year=campaign.year,
            user__in=users,
        )
    }

    to_create = []
    to_update = []

    for user in users:
        user_year = existing.get(user.id)

        if user_year is None:
            to_create.append(
                UserYear(
                    user=user,
                    year=campaign.year,
                    is_eligible=campaign.is_open,
                )
            )

        elif user_year.is_eligible != campaign.is_open:
            user_year.is_eligible = campaign.is_open and not user_year.is_exempted
            to_update.append(user_year)

    UserYear.objects.bulk_create(to_create)

    UserYear.objects.bulk_update(
        to_update,
        ["is_eligible"],
    )

    campaign.was_opened = campaign.is_open
    campaign.save(update_fields=["was_opened"])
