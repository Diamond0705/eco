from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("reports/archive/", views.archive, name="archive"),
    path("reports/archive/<int:pk>/download/", views.archive_download, name="archive_download"),
    path("reports/archive/<int:pk>/delete/", views.archive_delete, name="archive_delete"),
    path("reports/emissions/", views.emissions_report, name="emissions"),
    path("reports/emissions/pdf/", views.emissions_report_pdf, name="emissions_pdf"),
    path(
        "reports/emissions/pdf/archive/",
        views.emissions_report_pdf_archive,
        name="emissions_pdf_archive",
    ),
    path("reports/emissions/xlsx/", views.emissions_report_xlsx, name="emissions_xlsx"),
    path(
        "reports/emissions/xlsx/archive/",
        views.emissions_report_xlsx_archive,
        name="emissions_xlsx_archive",
    ),
]
