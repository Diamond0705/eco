from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("reports/emissions/", views.emissions_report, name="emissions"),
    path("reports/emissions/pdf/", views.emissions_report_pdf, name="emissions_pdf"),
    path("reports/emissions/xlsx/", views.emissions_report_xlsx, name="emissions_xlsx"),
]
