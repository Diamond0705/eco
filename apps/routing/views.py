from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from apps.core.permissions import manager_required
from apps.orders.models import ShipmentOrder
from apps.routing.models import RouteOption

from .services.provider_factory import EXTENDED_MODE, STANDARD_MODE
from .services.route_calculation_service import RouteCalculationService


def _manager_orders_queryset(request):
    return (
        ShipmentOrder.objects.filter(manager=request.user)
        .select_related("transport__eco_standard", "manager", "trip")
        .prefetch_related("points__location", "route_options")
    )


@manager_required
@require_POST
def calculate_routes(request, pk):
    order = get_object_or_404(_manager_orders_queryset(request), pk=pk)
    calculation_mode = _calculation_mode_from_request(request)
    service = RouteCalculationService(calculation_mode=calculation_mode)
    try:
        service.calculate_for_order(order)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("orders:detail", pk=order.pk)

    _store_route_diagnostics(request, order, service)
    if service.last_warning:
        messages.warning(request, service.last_warning)
    messages.success(request, "Маршруты рассчитаны.")
    return redirect("routing:options", pk=order.pk)


@manager_required
@require_GET
def route_options(request, pk):
    order = get_object_or_404(_manager_orders_queryset(request), pk=pk)
    points = order.points.all().order_by("sequence")
    route_options_list = list(order.route_options.all().order_by("created_at"))
    route_option_rows = _route_option_rows(route_options_list)
    route_diagnostics = _route_diagnostics(request, order, route_options_list)
    map_routes = [
        {
            "index": index,
            "name": route.name,
            "provider": route.provider,
            "provider_display": route.get_provider_display(),
            "eco_rating": str(route.eco_rating),
            "geometry_json": route.geometry_json,
        }
        for index, route in enumerate(route_options_list)
    ]
    return render(
        request,
        "routing/route_options.html",
        {
            "order": order,
            "points": points,
            "route_options": route_options_list,
            "route_option_rows": route_option_rows,
            "route_diagnostics": route_diagnostics,
            "map_routes": map_routes,
        },
    )


def _calculation_mode_from_request(request):
    if request.POST.get("route_calculation_mode") == EXTENDED_MODE:
        return EXTENDED_MODE
    return STANDARD_MODE


def _route_diagnostics_key(order):
    return f"route_calculation:{order.pk}"


def _store_route_diagnostics(request, order, service):
    request.session[_route_diagnostics_key(order)] = {
        "requested_count": service.last_requested_count,
        "found_count": service.last_found_count,
        "provider": service.last_used_provider,
    }


def _route_diagnostics(request, order, route_options):
    stored = request.session.get(_route_diagnostics_key(order), {})
    requested_count = stored.get("requested_count") or len(route_options)
    found_count = len(route_options)
    provider = stored.get("provider") or _single_provider(route_options)
    return {
        "requested_count": requested_count,
        "found_count": found_count,
        "provider": provider,
        "show_graphhopper_shortage": (
            provider == RouteOption.Provider.GRAPHHOPPER
            and requested_count
            and found_count < requested_count
        ),
    }


def _single_provider(route_options):
    providers = {route.provider for route in route_options}
    if len(providers) == 1:
        return providers.pop()
    return ""


def _route_option_rows(route_options):
    if not route_options:
        return []

    min_duration = min(route.duration_minutes for route in route_options)
    min_distance = min(route.distance_km for route in route_options)
    max_eco_rating = max(route.eco_rating for route in route_options)

    rows = []
    for route in route_options:
        badges = []
        if route.duration_minutes == min_duration:
            badges.append("Самый быстрый")
        if route.distance_km == min_distance:
            badges.append("Самый короткий")
        if route.eco_rating == max_eco_rating:
            badges.append("Лучший по эко-рейтингу")
        rows.append({"option": route, "badges": badges})
    return rows
