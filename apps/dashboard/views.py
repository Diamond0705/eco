from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from apps.core.permissions import admin_required, is_admin, is_manager, manager_required
from apps.fleet.models import EcoCalculationSettings, EcoStandard, Transport
from apps.locations.models import Location
from apps.reports.services.excel_export import TripExcelExportService, build_xlsx_response

from .forms import (
    AdminUserForm,
    EcoCalculationSettingsForm,
    EcoStandardForm,
    LocationForm,
    TransportForm,
)
from .services import AdminDashboardService, AnalyticsFilterParser, ManagerAnalyticsService

User = get_user_model()


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
@admin_required
def admin_dashboard_xlsx(request):
    analytics = AdminDashboardService().build()
    xlsx_bytes = TripExcelExportService().build_company_dashboard(analytics)
    return build_xlsx_response(xlsx_bytes, "company_dashboard.xlsx")


@require_GET
@admin_required
def admin_users(request):
    search_query = request.GET.get("q", "").strip()
    selected_active = request.GET.get("active", "").strip()
    users = User.objects.order_by("username")

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query)
            | Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
            | Q(middle_name__icontains=search_query)
            | Q(email__icontains=search_query)
        )
    users = _filter_active(users, selected_active)

    return render(
        request,
        "dashboard/admin_users.html",
        {
            "users": users,
            "search_query": search_query,
            "selected_active": selected_active,
        },
    )


@require_http_methods(["GET", "POST"])
@admin_required
def admin_user_edit(request, pk):
    edited_user = get_object_or_404(User, pk=pk)
    can_edit_activity = _can_edit_user_activity(request.user, edited_user)
    if request.method == "POST":
        if can_edit_activity:
            form = AdminUserForm(request.POST, instance=edited_user, current_user=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, "Активность пользователя обновлена.")
                return redirect("dashboard:admin_users")
        else:
            form = None
            messages.error(
                request,
                "Активность администратора изменяется только в расширенных настройках.",
            )
    else:
        form = (
            AdminUserForm(instance=edited_user, current_user=request.user)
            if can_edit_activity
            else None
        )

    return render(
        request,
        "dashboard/admin_user_form.html",
        {
            "form": form,
            "edited_user": edited_user,
            "can_edit_activity": can_edit_activity,
        },
    )


@require_GET
@admin_required
def admin_transports(request):
    search_query = request.GET.get("q", "").strip()
    selected_eco_standard = request.GET.get("eco_standard", "").strip()
    transports = Transport.objects.select_related("eco_standard").order_by("plate_number")
    eco_standards = EcoStandard.objects.order_by("name")

    if search_query:
        transports = transports.filter(
            Q(plate_number__icontains=search_query) | Q(model__icontains=search_query)
        )
    if selected_eco_standard.isdigit():
        transports = transports.filter(eco_standard_id=int(selected_eco_standard))

    return render(
        request,
        "dashboard/admin_transports.html",
        {
            "transports": transports,
            "search_query": search_query,
            "selected_eco_standard": selected_eco_standard,
            "eco_standards": eco_standards,
        },
    )


@require_http_methods(["GET", "POST"])
@admin_required
def admin_transport_create(request):
    if request.method == "POST":
        form = TransportForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Транспорт создан.")
            return redirect("dashboard:admin_transports")
    else:
        form = TransportForm()

    return render(
        request,
        "dashboard/admin_transport_form.html",
        {"form": form, "is_create": True},
    )


@require_http_methods(["GET", "POST"])
@admin_required
def admin_transport_edit(request, pk):
    transport = get_object_or_404(Transport, pk=pk)
    if request.method == "POST":
        form = TransportForm(request.POST, instance=transport)
        if form.is_valid():
            form.save()
            messages.success(request, "Транспорт обновлен.")
            return redirect("dashboard:admin_transports")
    else:
        form = TransportForm(instance=transport)

    return render(
        request,
        "dashboard/admin_transport_form.html",
        {"form": form, "transport": transport, "is_create": False},
    )


@require_GET
@admin_required
def admin_locations(request):
    search_query = request.GET.get("q", "").strip()
    selected_active = request.GET.get("active", "").strip()
    locations = Location.objects.order_by("name")

    if search_query:
        locations = locations.filter(
            Q(name__icontains=search_query) | Q(address__icontains=search_query)
        )
    locations = _filter_active(locations, selected_active)

    return render(
        request,
        "dashboard/admin_locations.html",
        {
            "locations": locations,
            "search_query": search_query,
            "selected_active": selected_active,
        },
    )


@require_http_methods(["GET", "POST"])
@admin_required
def admin_location_create(request):
    if request.method == "POST":
        form = LocationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Локация создана.")
            return redirect("dashboard:admin_locations")
    else:
        form = LocationForm()

    return render(
        request,
        "dashboard/admin_location_form.html",
        {"form": form, "is_create": True},
    )


@require_http_methods(["GET", "POST"])
@admin_required
def admin_location_edit(request, pk):
    location = get_object_or_404(Location, pk=pk)
    if request.method == "POST":
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            messages.success(request, "Локация обновлена.")
            return redirect("dashboard:admin_locations")
    else:
        form = LocationForm(instance=location)

    return render(
        request,
        "dashboard/admin_location_form.html",
        {"form": form, "location": location, "is_create": False},
    )


@require_GET
@admin_required
def admin_eco_standards(request):
    search_query = request.GET.get("q", "").strip()
    selected_active = request.GET.get("active", "").strip()
    standards = EcoStandard.objects.order_by("name")

    if search_query:
        standards = standards.filter(name__icontains=search_query)
    standards = _filter_active(standards, selected_active)

    return render(
        request,
        "dashboard/admin_eco_standards.html",
        {
            "standards": standards,
            "search_query": search_query,
            "selected_active": selected_active,
        },
    )


@require_http_methods(["GET", "POST"])
@admin_required
def admin_eco_standard_create(request):
    if request.method == "POST":
        form = EcoStandardForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Экологический стандарт создан.")
            return redirect("dashboard:admin_eco_standards")
    else:
        form = EcoStandardForm()

    return render(
        request,
        "dashboard/admin_eco_standard_form.html",
        {"form": form, "is_create": True},
    )


@require_http_methods(["GET", "POST"])
@admin_required
def admin_eco_standard_edit(request, pk):
    standard = get_object_or_404(EcoStandard, pk=pk)
    if request.method == "POST":
        form = EcoStandardForm(request.POST, instance=standard)
        if form.is_valid():
            form.save()
            messages.success(request, "Экологический стандарт обновлен.")
            return redirect("dashboard:admin_eco_standards")
    else:
        form = EcoStandardForm(instance=standard)

    return render(
        request,
        "dashboard/admin_eco_standard_form.html",
        {"form": form, "standard": standard, "is_create": False},
    )


@require_GET
@admin_required
def admin_calculation_settings(request):
    current_settings = EcoCalculationSettings.get_current()
    settings_versions = EcoCalculationSettings.objects.order_by("-created_at")

    return render(
        request,
        "dashboard/admin_calculation_settings.html",
        {
            "current_settings": current_settings,
            "settings_versions": settings_versions,
        },
    )


@require_http_methods(["GET", "POST"])
@admin_required
def admin_calculation_settings_create(request):
    if request.method == "POST":
        form = EcoCalculationSettingsForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Новая версия настроек экологического расчета создана.")
            return redirect("dashboard:admin_calculation_settings")
    else:
        initial = {
            **EcoCalculationSettings.default_values(),
            "name": "",
            "is_active": "1",
        }
        form = EcoCalculationSettingsForm(initial=initial)

    return render(
        request,
        "dashboard/admin_calculation_settings_form.html",
        {"form": form, "is_create": True, "settings_version": None},
    )


@require_http_methods(["GET", "POST"])
@admin_required
def admin_calculation_settings_edit(request, pk):
    settings_version = get_object_or_404(EcoCalculationSettings, pk=pk)
    if request.method == "POST":
        form = EcoCalculationSettingsForm(request.POST, instance=settings_version)
        if form.is_valid():
            form.save()
            messages.success(request, "Версия настроек экологического расчета обновлена.")
            return redirect("dashboard:admin_calculation_settings")
    else:
        form = EcoCalculationSettingsForm(instance=settings_version)

    return render(
        request,
        "dashboard/admin_calculation_settings_form.html",
        {"form": form, "is_create": False, "settings_version": settings_version},
    )


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


def _filter_active(queryset, selected_active):
    if selected_active == "1":
        return queryset.filter(is_active=True)
    if selected_active == "0":
        return queryset.filter(is_active=False)
    return queryset


def _can_edit_user_activity(current_user, edited_user):
    if edited_user.pk == current_user.pk:
        return False
    if edited_user.is_superuser or getattr(edited_user, "role", None) == User.Role.ADMIN:
        return False
    return True
