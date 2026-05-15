from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET

from apps.core.permissions import admin_required, is_admin, is_manager, manager_required

from .services import AdminDashboardService, AnalyticsFilterParser, ManagerAnalyticsService


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
    analytics = ManagerAnalyticsService().build(request.user)
    return render(request, "dashboard/manager_dashboard.html", {"analytics": analytics})


@require_GET
@admin_required
def admin_dashboard(request):
    analytics = AdminDashboardService().build()
    return render(request, "dashboard/admin_dashboard.html", {"analytics": analytics})


@require_GET
@manager_required
def manager_analytics(request):
    filters = AnalyticsFilterParser().parse(request.GET)
    analytics = ManagerAnalyticsService().build(request.user, filters)
    return render(
        request,
        "dashboard/manager_analytics.html",
        {
            "analytics": analytics,
            "filters": filters,
            "date_from": request.GET.get("date_from", ""),
            "date_to": request.GET.get("date_to", ""),
        },
    )
