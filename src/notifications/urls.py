from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="notifications"),
    path("reminders/", views.reminders, name="reminders"),
]