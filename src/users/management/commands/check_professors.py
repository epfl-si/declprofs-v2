import os
import requests

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from auditlogs.models import ActivityLog
from users.models import UserYear

User = get_user_model()


class Command(BaseCommand):
    help = "Import professors from EPFL API and check if they are still employed"

    def get_api_auth(self):
        return (
            os.getenv("DJANGO_SERVICE_ACCOUNT_NAME"),
            os.getenv("DJANGO_SERVICE_ACCOUNT_PASSWORD"),
        )

    def get_user_name_and_unit(self, sciper):
        url = f"https://api.epfl.ch/v1/accreds?persid={sciper}"

        response = requests.get(
            url,
            auth=self.get_api_auth(),
            headers={
                "Accept": "application/json"
            },
        )

        response.raise_for_status()

        data = response.json()

        accreds = data.get("accreds", [])

        for accred in accreds:
            person = accred.get("person", {})

            if person.get("email") and accred.get("order") == 1:
                unit = accred.get("unit", {}).get("path", "")
                firstname = person.get("firstname", {})
                lastname = person.get("lastname", {})
                return [firstname, lastname, unit]

        return ["", "", ""]

    def handle(self, *args, **options):

        url = "https://api.epfl.ch/v1/groups/S16395/members?pagesize=0"

        response = requests.get(
            url,
            auth=self.get_api_auth(),
            headers={
                "Accept": "application/json",
            },
        )

        response.raise_for_status()

        data = response.json()
        members = data["members"]

        current_year = timezone.now().year

        created = 0
        updated = 0
        employed = 0
        not_employed = 0

        member_scipers = set()

        for member in members:

            if member.get("type") != "person":
                continue

            if "email" not in member:
                continue

            sciper = member["id"]
            member_scipers.add(sciper)

            name_and_unit = self.get_user_name_and_unit(sciper)

            user, was_created = User.objects.update_or_create(
                sciper=sciper,
                defaults={
                    "username": member["username"],
                    "email": member["email"],
                    "first_name": name_and_unit[0],
                    "last_name": name_and_unit[1],
                    "unit": name_and_unit[2],
                    "has_access": True,
                },
            )

            if was_created:
                user.set_unusable_password()
                user.save(update_fields=["password"])

                ActivityLog.objects.create(
                    user=None,
                    activity=None,
                    action=ActivityLog.Action.CREATED,
                    changes={
                        "user": "Cron",
                        "Professor": str(user),
                        "sciper": user.sciper,
                        "email": user.email,
                    },
                )

                created += 1
            else:
                updated += 1

            user_year, _ = UserYear.objects.get_or_create(
                user=user,
                year=current_year,
            )

            if not user_year.is_employed:
                user_year.is_employed = True
                user_year.save(update_fields=["is_employed"])

            employed += 1

        users_not_in_members = User.objects.exclude(
            sciper__in=member_scipers
        )

        for user in users_not_in_members:

            if user.is_superuser:
                continue

            user_year = UserYear.objects.filter(
                user=user,
                year=current_year,
            ).first()

            if user_year is None:
                continue

            if user_year.is_employed:
                user_year.is_employed = False
                user_year.save(update_fields=["is_employed"])

            not_employed += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Import finished: "
                f"{created} created, "
                f"{updated} updated, "
                f"{employed} employed, "
                f"{not_employed} not employed"
            )
        )
