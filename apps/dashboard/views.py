from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET

from apps.core.permissions import admin_required, is_admin, is_manager, manager_required


@require_GET
def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard:dashboard")
    return redirect("accounts:login")


@require_GET
def dashboard_redirect(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    if is_admin(request.user):
        return redirect("dashboard:admin_dashboard")
    if is_manager(request.user):
        return redirect("dashboard:manager_dashboard")
    raise PermissionDenied


@require_GET
@manager_required
def manager_dashboard(request):
    return render(request, "dashboard/manager_dashboard.html")


@require_GET
@admin_required
def admin_dashboard(request):
    return render(request, "dashboard/admin_dashboard.html")
