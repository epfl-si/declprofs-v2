from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Activity

User = get_user_model()


class ActivityForm(forms.ModelForm):

    class Meta:
        model = Activity
        fields = [
            "user",
            "activity",
            "principal",
            "comments",
            "comments_apr",
            "date_start",
            "date_end",
        ]
        widgets = {
            "user": forms.Select(attrs={
                "class": "form-control select2-user",
            }),
            "activity": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 1,
            }),
            "principal": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 1,
            }),
            "comments": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 1,
            }),
            "comments_apr": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 1,
            }),
            "date_start": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),
            "date_end": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),
        }

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop("current_user", None)
        super().__init__(*args, **kwargs)

        if self.current_user and not self.current_user.is_superuser:
            self.fields["user"].required = False
            self.fields["user"].widget = forms.HiddenInput()
            self.initial["user"] = self.current_user

        else:
            self.fields["user"].queryset = User.objects.order_by(
                "last_name",
                "first_name",
            )

        if not self.instance.pk:
            self.fields["date_start"].initial = timezone.now()

        for field_name, field in self.fields.items():
            if field_name in self.errors and not isinstance(
                field.widget,
                forms.HiddenInput
            ):
                current_class = field.widget.attrs.get("class", "")
                field.widget.attrs["class"] = (
                    f"{current_class} is-invalid"
                ).strip()
