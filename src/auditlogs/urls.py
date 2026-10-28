from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="auditlogs"),
    path("email-logs/", views.email_logs, name="emaillogs"),
]
