from decimal import Decimal

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from apps.core.permissions import manager_required
from apps.orders.models import ShipmentOrder
from apps.routing.models import RouteOption

from .services.provider_factory import EXTENDED_MODE, STANDARD_MODE
from .services.route_calculation_service import RouteCalculationService

TOLL_WARNING = (
    "На маршруте есть платные участки. Их стоимость не включена в итоговую стоимость перевозки."
)
LEGACY_TOLL_WARNING = (
    "Маршрут содержит платные участки, но стоимость проезда не рассчитана провайдером "
    "и не включена в итоговую стоимость перевозки."
)
NO_TRAFFIC_WARNING = "Провайдер не предоставляет данные о пробках, traffic_factor=1.00."


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
            "name": row["display_name"],
            "provider": row["option"].provider,
            "provider_display": row["option"].get_provider_display(),
            "eco_rating": str(row["option"].eco_rating),
            "geometry_json": row["option"].geometry_json,
        }
        for index, row in enumerate(route_option_rows)
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
    max_eco_routes = [route for route in route_options if route.eco_rating == max_eco_rating]
    best_eco_route = max_eco_routes[0] if len(max_eco_routes) == 1 else None

    rows = []
    for index, route in enumerate(route_options, start=1):
        badges = []
        if route.duration_minutes == min_duration:
            badges.append("Самый быстрый")
        if route.distance_km == min_distance:
            badges.append("Самый короткий")
        if route == best_eco_route:
            badges.append("Лучший по эко-рейтингу")
        elif route.eco_rating == max_eco_rating:
            badges.append("Одинаковый эко-рейтинг")
        rows.append(
            {
                "option": route,
                "display_name": f"Маршрут {index}",
                "badges": badges,
                "calculation_details": _calculation_details(route),
                "warnings": _calculation_warnings(route),
                "has_unpriced_tolls": _has_unpriced_tolls(route),
            }
        )
    return rows


def _calculation_details(route):
    details = route.calculation_details_json
    if not isinstance(details, dict):
        details = {}
    return {
        "calculation_model_version": details.get(
            "calculation_model_version",
            route.calculation_model_version,
        ),
        "final_fuel_multiplier": details.get("final_fuel_multiplier", route.fuel_multiplier),
        "average_speed_kmh": details.get("average_speed_kmh", "—"),
        "road_class_factor": details.get("road_class_factor", "—"),
        "surface_factor": details.get("surface_factor", "—"),
        "traffic_factor": details.get("traffic_factor", "—"),
    }


def _calculation_warnings(route):
    route_facts = route.route_facts_json
    if not isinstance(route_facts, dict):
        route_facts = {}
    details = route.calculation_details_json
    if not isinstance(details, dict):
        details = {}

    warnings = []
    route_fact_warnings = route_facts.get("warnings", [])
    if isinstance(route_fact_warnings, list):
        warnings.extend(route_fact_warnings)
    detail_warnings = details.get("warnings", [])
    if isinstance(detail_warnings, list):
        warnings.extend(detail_warnings)
    if _has_unpriced_tolls(route):
        warnings.append(TOLL_WARNING)
    return _deduplicate_items(warnings)


def _has_unpriced_tolls(route):
    route_facts = route.route_facts_json
    if not isinstance(route_facts, dict):
        return False
    return route_facts.get("has_tolls") and _decimal_from_json(
        route_facts.get("toll_cost_rub", "0.00")
    ) == Decimal("0.00")


def _decimal_from_json(value):
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0.00")


def _deduplicate_items(items):
    unique_items = []
    seen = set()
    for item in items:
        if not item or item in seen:
            continue
        if item == LEGACY_TOLL_WARNING:
            item = TOLL_WARNING
            if item in seen:
                continue
        if item == NO_TRAFFIC_WARNING:
            continue
        seen.add(item)
        unique_items.append(item)
    return unique_items
