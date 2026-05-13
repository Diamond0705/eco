from django.contrib import admin

from .models import Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "latitude", "longitude", "is_active")
    search_fields = ("name", "address")
    list_filter = ("is_active",)
    ordering = ("name",)
