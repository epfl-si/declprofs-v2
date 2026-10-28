from django.contrib import admin

from .models import Activity


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = (
        "activity",
        "user",
        "status",
        "principal",
        "date_start",
        "date_end",
    )

    search_fields = (
        "status",
        "activity",
        "principal",
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "user__sciper",
    )

    list_filter = (
        "date_start",
        "date_end",
    )

    ordering = (
        "-date_start",
    )

    fieldsets = (
        (
            "Activity information",
            {
                "fields": (
                    "status",
                    "user",
                    "activity",
                    "principal",
                    "date_start",
                    "date_end",
                )
            },
        ),
        (
            "Comments",
            {
                "fields": (
                    "comments",
                    "comments_apr",
                )
            },
        ),
    )
