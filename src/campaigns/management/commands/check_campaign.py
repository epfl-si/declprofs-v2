from django.core.management.base import BaseCommand
from django.utils import timezone

from campaigns.models import Campaign
from campaigns.services import update_user_years_for_campaign


class Command(BaseCommand):
    help = "Check all campaigns and update users eligibility when needed."

    def handle(self, *args, **options):
        campaigns = Campaign.objects.all()

        if not campaigns.exists():
            self.stdout.write(
                self.style.WARNING("No campaign found.")
            )
            return

        now = timezone.now()

        for campaign in campaigns:
            self.stdout.write(
                f"Checking campaign {campaign.year}..."
            )

            if campaign.is_open:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Campaign {campaign.year} is currently open."
                    )
                )

                was_opened = campaign.was_opened

                if not was_opened:
                    self.stdout.write("Updating user years...")

                if campaign.was_opened != campaign.is_open:
                    update_user_years_for_campaign(campaign)

                if not was_opened:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"User years updated for campaign {campaign.year}."
                        )
                    )

            elif now > campaign.closing_date:
                self.stdout.write(
                    f"Campaign {campaign.year} is closed."
                )

                was_opened = campaign.was_opened

                if was_opened:
                    self.stdout.write("Updating user years...")

                if campaign.was_opened != campaign.is_open:
                    update_user_years_for_campaign(campaign)

                if was_opened:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"User years updated for campaign {campaign.year}."
                        )
                    )
