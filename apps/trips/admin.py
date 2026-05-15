from django.contrib import admin

from .models import Trip, TripStatusEvent


class TripStatusEventInline(admin.TabularInline):
    model = TripStatusEvent
    extra = 0
    fields = ("old_status", "new_status", "changed_by", "event_at", "changed_at", "comment")
    readonly_fields = ("changed_at",)
    ordering = ("changed_at",)


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "route_option",
        "status",
        "planned_start_at",
        "actual_start_at",
        "actual_finish_at",
        "created_at",
    )
    search_fields = (
        "id",
        "order__id",
        "order__cargo_name",
        "order__manager__username",
        "route_option__name",
    )
    list_filter = ("status", "created_at", "updated_at")
    ordering = ("-created_at",)
    inlines = (TripStatusEventInline,)


@admin.register(TripStatusEvent)
class TripStatusEventAdmin(admin.ModelAdmin):
    list_display = ("trip", "old_status", "new_status", "changed_by", "event_at", "changed_at")
    search_fields = ("trip__id", "trip__order__cargo_name", "changed_by__username", "comment")
    list_filter = ("new_status", "event_at", "changed_at")
    ordering = ("-changed_at",)
