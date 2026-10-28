from django.contrib import admin

from .models import Campaign


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = (
        "year",
        "opening_date",
        "closing_date",
        "was_opened",
    )
    list_display_links = ("year",)
    ordering = ("-year",)
    search_fields = ("year",)

    fieldsets = (
        (
            "Campaign",
            {
                "fields": (
                    "year",
                    "opening_date",
                    "closing_date",
                    "was_opened",
                )
            },
        ),
    )
