from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("orders/", views.order_list, name="list"),
    path("orders/create/", views.order_create, name="create"),
    path("orders/<int:pk>/", views.order_detail, name="detail"),
    path("orders/<int:pk>/edit/", views.order_edit, name="edit"),
    path("orders/<int:pk>/cancel/", views.order_cancel, name="cancel"),
]
