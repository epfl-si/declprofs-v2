from tinymce.widgets import TinyMCE

from django import forms
from django.forms import modelformset_factory

from .models import Notification


class NotificationForm(forms.ModelForm):

    class Meta:
        model = Notification
        fields = [
            "subject",
            "body",
            "test_to",
            "prod_to",
            "test_cc",
            "prod_cc",
            "test_bcc",
            "prod_bcc",
        ]

        widgets = {
            "subject": forms.Textarea(
                attrs={"rows": 1, "class": "form-control",}
            ),
            "body": TinyMCE(
                attrs={"class": "tinymce",},
                mce_attrs={
                    "height": 300,
                    "menubar": False,
                    "plugins": (
                        "advlist autolink lists link "
                        "charmap searchreplace visualblocks "
                        "code fullscreen"
                    ),
                    "toolbar": (
                        "undo redo | "
                        "blocks | "
                        "bold italic underline | "
                        "alignleft aligncenter alignright | "
                        "bullist numlist | "
                        "link | "
                        "code fullscreen"
                    ),
                    "branding": False,
                    "license_key": "gpl",
                },
            ),
            "test_to": forms.Textarea(
                attrs={"rows": 1, "class": "form-control",}
            ),
            "prod_to": forms.Textarea(
                attrs={"rows": 1, "class": "form-control",}
            ),
            "test_cc": forms.Textarea(
                attrs={"rows": 1, "class": "form-control",}
            ),
            "prod_cc": forms.Textarea(
                attrs={"rows": 1, "class": "form-control",}
            ),
            "test_bcc": forms.Textarea(
                attrs={"rows": 1, "class": "form-control",}
            ),
            "prod_bcc": forms.Textarea(
                attrs={"rows": 1, "class": "form-control",}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ""


NotificationFormSet = modelformset_factory(
    Notification,
    form=NotificationForm,
    extra=0,
)
