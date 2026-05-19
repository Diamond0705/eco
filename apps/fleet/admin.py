from django.contrib import admin

from .models import EcoCalculationSettings, EcoStandard, Transport


@admin.register(EcoStandard)
class EcoStandardAdmin(admin.ModelAdmin):
    list_display = ("name", "nox_limit_g_per_kwh", "pm_limit_mg_per_kwh", "is_active")
    search_fields = ("name",)
    list_filter = ("is_active",)
    ordering = ("name",)


@admin.register(Transport)
class TransportAdmin(admin.ModelAdmin):
    list_display = (
        "plate_number",
        "model",
        "category",
        "fuel_type",
        "capacity_kg",
        "fuel_consumption_l_per_100km",
        "eco_standard",
        "year",
        "is_active",
    )
    search_fields = ("plate_number", "model")
    list_filter = ("category", "fuel_type", "eco_standard", "is_active")
    ordering = ("plate_number",)


@admin.register(EcoCalculationSettings)
class EcoCalculationSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "is_active",
        "diesel_co2_kg_per_liter",
        "fuel_price_rub_per_liter",
        "service_tariff_rub_per_km",
        "driver_time_tariff_rub_per_hour",
        "updated_at",
    )
    search_fields = ("name",)
    list_filter = ("is_active",)
    ordering = ("-created_at",)
