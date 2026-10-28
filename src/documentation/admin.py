from django.contrib import admin
from tinymce.widgets import TinyMCE

from .models import Documentation


@admin.register(Documentation)
class DocumentationAdmin(admin.ModelAdmin):
    list_display = ("title", "type", "order", "updated_at")

    class Media:
        js = ("documentation/js/tinymce_upload.js",)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "content":
            kwargs["widget"] = TinyMCE(
                attrs={
                    "style": "width: 100%; min-height: 500px;",
                },
                mce_attrs={
                    "images_upload_handler": "uploadImage",
                },
            )

        return super().formfield_for_dbfield(
            db_field,
            request,
            **kwargs,
        )
