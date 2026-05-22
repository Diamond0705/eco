from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("dashboard/", views.dashboard_redirect, name="dashboard"),
    path("manager/dashboard/", views.manager_dashboard, name="manager_dashboard"),
    path("analytics/", views.manager_analytics, name="manager_analytics"),
    path("admin-panel/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-panel/dashboard/xlsx/", views.admin_dashboard_xlsx, name="admin_dashboard_xlsx"),
    path(
        "admin-panel/dashboard/xlsx/archive/",
        views.admin_dashboard_xlsx_archive,
        name="admin_dashboard_xlsx_archive",
    ),
    path("admin-panel/users/", views.admin_users, name="admin_users"),
    path("admin-panel/users/<int:pk>/edit/", views.admin_user_edit, name="admin_user_edit"),
    path("admin-panel/transports/", views.admin_transports, name="admin_transports"),
    path(
        "admin-panel/transports/create/",
        views.admin_transport_create,
        name="admin_transport_create",
    ),
    path(
        "admin-panel/transports/<int:pk>/edit/",
        views.admin_transport_edit,
        name="admin_transport_edit",
    ),
    path("admin-panel/locations/", views.admin_locations, name="admin_locations"),
    path(
        "admin-panel/locations/create/",
        views.admin_location_create,
        name="admin_location_create",
    ),
    path(
        "admin-panel/locations/<int:pk>/edit/",
        views.admin_location_edit,
        name="admin_location_edit",
    ),
    path(
        "admin-panel/eco-standards/",
        views.admin_eco_standards,
        name="admin_eco_standards",
    ),
    path(
        "admin-panel/eco-standards/create/",
        views.admin_eco_standard_create,
        name="admin_eco_standard_create",
    ),
    path(
        "admin-panel/eco-standards/<int:pk>/edit/",
        views.admin_eco_standard_edit,
        name="admin_eco_standard_edit",
    ),
    path(
        "admin-panel/calculation-settings/",
        views.admin_calculation_settings,
        name="admin_calculation_settings",
    ),
    path(
        "admin-panel/calculation-settings/create/",
        views.admin_calculation_settings_create,
        name="admin_calculation_settings_create",
    ),
    path(
        "admin-panel/calculation-settings/<int:pk>/edit/",
        views.admin_calculation_settings_edit,
        name="admin_calculation_settings_edit",
    ),
]
