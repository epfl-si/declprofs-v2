from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="campaign"),
    path("by-year/", views.campaign_by_year, name="campaign_by_year"),
]