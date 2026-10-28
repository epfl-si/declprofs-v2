from django.contrib import admin

from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "action",
        "changes_user",
        "user",
        "activity",
        "changes",
    )

    list_filter = (
        "action",
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "activity__title",
    )

    readonly_fields = (
        "activity",
        "user",
        "action",
        "changes",
        "created_at",
    )

    ordering = (
        "-created_at",
    )

    @admin.display(description="Owner")
    def changes_user(self, obj):
        return obj.changes.get("user", "-")
