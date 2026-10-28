from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, UserYear


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):

    fieldsets = (
        (
            "Personal information",
            {
                "fields": (
                    "username",
                    "first_name",
                    "last_name",
                    "email",
                    "sciper",
                    "unit",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                    "has_access",
                )
            },
        ),
        (
            "Important dates",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                )
            },
        ),
    )

    readonly_fields = (
        "last_login",
        "date_joined",
    )

    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
        "sciper",
        "unit",
        "has_access",
    )

    list_display = (
        "username",
        "first_name",
        "last_name",
        "email",
        "sciper",
        "unit",
        "is_active",
        "is_staff",
        "is_superuser",
        "has_access",
    )

    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
        "has_access",
    )

    ordering = (
        "last_name",
        "first_name",
    )


@admin.register(UserYear)
class UserYearAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "year",
        "is_eligible",
        "is_exempted",
        "is_employed",
        "draft_count",
        "missing_count",
        "submitted_count",
        "updated_at",
        "reminder_at",
    )

    list_filter = (
        "year",
        "is_eligible",
        "is_exempted",
        "is_employed",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "user__sciper",
    )

    readonly_fields = (
        "updated_at",
        "reminder_at",
    )

    ordering = (
        "-year",
        "user__last_name",
        "user__first_name",
    )

    fieldsets = (
        (
            "User and campaign",
            {
                "fields": (
                    "user",
                    "year",
                )
            },
        ),
        (
            "Eligibility",
            {
                "fields": (
                    "is_eligible",
                    "is_exempted",
                    "is_employed",
                )
            },
        ),
        (
            "Submission counters",
            {
                "fields": (
                    "draft_count",
                    "missing_count",
                    "submitted_count",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "updated_at",
                    "reminder_at",
                )
            },
        ),
    )

