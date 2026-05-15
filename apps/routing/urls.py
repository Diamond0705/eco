from django.urls import path

from . import views

app_name = "routing"

urlpatterns = [
    path("orders/<int:pk>/calculate-routes/", views.calculate_routes, name="calculate"),
    path("orders/<int:pk>/routes/", views.route_options, name="options"),
]
