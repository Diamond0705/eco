from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class EcoLogistUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Профиль EcoLogist", {"fields": ("middle_name", "phone", "role")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Профиль EcoLogist", {"fields": ("middle_name", "phone", "role")}),
    )
    list_display = ("username", "email", "first_name", "last_name", "role", "is_staff")
    list_filter = UserAdmin.list_filter + ("role",)
