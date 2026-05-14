from django.contrib import admin

from .models import OrderPoint, ShipmentOrder


class OrderPointInline(admin.TabularInline):
    model = OrderPoint
    extra = 0
    fields = ("sequence", "point_type", "location")
    ordering = ("sequence",)


@admin.register(ShipmentOrder)
class ShipmentOrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "manager",
        "cargo_name",
        "cargo_type",
        "cargo_weight_kg",
        "transport",
        "desired_delivery_date",
        "status",
        "created_at",
    )
    search_fields = (
        "id",
        "manager__username",
        "manager__email",
        "cargo_name",
        "cargo_type",
        "transport__plate_number",
        "transport__model",
    )
    list_filter = ("status", "transport", "desired_delivery_date", "created_at")
    ordering = ("-created_at",)
    inlines = (OrderPointInline,)


@admin.register(OrderPoint)
class OrderPointAdmin(admin.ModelAdmin):
    list_display = ("order", "sequence", "point_type", "location", "created_at")
    search_fields = ("order__id", "location__name", "location__address")
    list_filter = ("point_type", "location")
    ordering = ("order", "sequence")
