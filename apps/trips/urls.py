from django.urls import path

from apps.reports import views as report_views

from . import views

app_name = "trips"

urlpatterns = [
    path(
        "orders/<int:order_id>/routes/<int:route_option_id>/approve/",
        views.approve_route,
        name="approve_route",
    ),
    path("trips/", views.trip_list, name="list"),
    path("trips/export/xlsx/", report_views.trips_xlsx, name="export_xlsx"),
    path("trips/export/xlsx/archive/", report_views.trips_xlsx_archive, name="export_xlsx_archive"),
    path("trips/<int:pk>/", views.trip_detail, name="detail"),
    path("trips/<int:pk>/waybill/", report_views.trip_waybill, name="waybill"),
    path(
        "trips/<int:pk>/waybill/archive/",
        report_views.trip_waybill_archive,
        name="waybill_archive",
    ),
    path("trips/<int:pk>/start/", views.trip_start, name="start"),
    path("trips/<int:pk>/deliver/", views.trip_deliver, name="deliver"),
]
