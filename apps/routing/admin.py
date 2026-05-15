from django.contrib import admin

from .models import RouteOption


@admin.register(RouteOption)
class RouteOptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "name",
        "provider",
        "distance_km",
        "duration_minutes",
        "cost_rub",
        "eco_rating",
        "is_selected",
        "created_at",
    )
    search_fields = ("id", "order__id", "order__cargo_name", "name")
    list_filter = ("provider", "is_selected", "created_at")
    ordering = ("-created_at",)
