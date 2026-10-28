from django import forms
from .models import Campaign


class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = [
            "year",
            "opening_date",
            "closing_date",
        ]

        widgets = {
            "year": forms.NumberInput(
                attrs={"min": "1900", "class": "form-control",}
            ),
            "opening_date": forms.DateTimeInput(
                attrs={"type": "datetime-local", "step": "1", "class": "form-control",}
            ),
            "closing_date": forms.DateTimeInput(
                attrs={"type": "datetime-local", "step": "1", "class": "form-control",}
            ),
        }
