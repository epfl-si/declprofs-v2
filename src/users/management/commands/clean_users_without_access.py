from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Delete users who do not have access (has_access == False)."

    def handle(self, *args, **options):

        users = User.objects.filter(
            has_access=False,
        )

        count = users.count()

        users.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"{count} user(s) deleted."
            )
        )
