import os
import requests

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


User = get_user_model()


class Command(BaseCommand):
    help = "Import professors from EPFL API"

    def get_api_auth(self):
        return (
            os.getenv("DJANGO_SERVICE_ACCOUNT_NAME"),
            os.getenv("DJANGO_SERVICE_ACCOUNT_PASSWORD"),
        )

    def get_user_unit(self, sciper):
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
                unit = accred.get("unit", {})
                return unit.get("path", "")

        return ""

    def handle(self, *args, **options):

        url = "https://api.epfl.ch/v1/groups/S16395/members?pagesize=0"

        response = requests.get(
            url,
            auth=self.get_api_auth(),
            headers={
                "Accept": "application/json"
            },
        )

        response.raise_for_status()

        data = response.json()

        members = data["members"]

        created = 0
        updated = 0

        for member in members:

            if member.get("type") != "person":
                continue

            if "email" not in member:
                continue

            sciper = member["id"]

            unit = self.get_user_unit(sciper)

            display = member.get("display", "").split(" ", 1)

            last_name = display[0] if len(display) > 0 else ""
            first_name = display[1] if len(display) > 1 else ""

            user, was_created = User.objects.update_or_create(
                sciper=sciper,
                defaults={
                    "username": member["username"],
                    "email": member["email"],
                    "first_name": first_name,
                    "last_name": last_name,
                    "unit": unit,
                    "has_access": True,
                },
            )

            if was_created:
                user.set_unusable_password()
                user.save()
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Import finished : {created} created, {updated} updated"
            )
        )
