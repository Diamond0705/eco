from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from apps.core.permissions import manager_required
from apps.orders.models import ShipmentOrder

from .services.route_calculation_service import RouteCalculationService


def _manager_orders_queryset(request):
    return (
        ShipmentOrder.objects.filter(manager=request.user)
        .select_related("transport__eco_standard", "manager")
        .prefetch_related("points__location", "route_options")
    )


@manager_required
@require_POST
def calculate_routes(request, pk):
    order = get_object_or_404(_manager_orders_queryset(request), pk=pk)
    try:
        RouteCalculationService().calculate_for_order(order)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("orders:detail", pk=order.pk)

    messages.success(request, "Маршруты рассчитаны.")
    return redirect("routing:options", pk=order.pk)


@manager_required
@require_GET
def route_options(request, pk):
    order = get_object_or_404(_manager_orders_queryset(request), pk=pk)
    points = order.points.all().order_by("sequence")
    route_options_queryset = order.route_options.all().order_by("created_at")
    map_routes = [
        {
            "name": route.name,
            "eco_rating": str(route.eco_rating),
            "geometry_json": route.geometry_json,
        }
        for route in route_options_queryset
    ]
    return render(
        request,
        "routing/route_options.html",
        {
            "order": order,
            "points": points,
            "route_options": route_options_queryset,
            "map_routes": map_routes,
        },
    )
