from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("name", "subject")
    search_fields = ("name", "subject")

    fieldsets = (
        (
            "General",
            {
                "fields": (
                    "name",
                    "subject",
                    "body",
                )
            },
        ),
        (
            "Test recipients",
            {
                "fields": (
                    "test_to",
                    "test_cc",
                    "test_bcc",
                )
            },
        ),
        (
            "Production recipients",
            {
                "fields": (
                    "prod_to",
                    "prod_cc",
                    "prod_bcc",
                )
            },
        ),
    )
