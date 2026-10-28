from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("report/", views.disclosure_report, name="disclosure_report"),
    path("csv/", views.report_csv, name="report_csv"),
]
