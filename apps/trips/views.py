from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from apps.core.permissions import manager_required
from apps.orders.models import ShipmentOrder
from apps.routing.models import RouteOption

from .models import Trip
from .services import TripLifecycleService


def _manager_orders_queryset(request):
    return (
        ShipmentOrder.objects.filter(manager=request.user)
        .select_related("manager")
        .prefetch_related("route_options")
    )


def _manager_trips_queryset(request):
    return (
        Trip.objects.filter(order__manager=request.user)
        .select_related(
            "order",
            "order__transport",
            "route_option",
            "route_option__calculation_settings",
        )
        .prefetch_related("status_events__changed_by")
    )


@manager_required
@require_POST
def approve_route(request, order_id, route_option_id):
    order = get_object_or_404(_manager_orders_queryset(request), pk=order_id)
    route_option = get_object_or_404(RouteOption.objects.filter(order=order), pk=route_option_id)

    if hasattr(order, "trip"):
        messages.error(request, "Для этой заявки уже создан рейс.")
        return redirect("trips:detail", pk=order.trip.pk)

    try:
        trip = TripLifecycleService().approve_route(order, route_option, request.user)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("routing:options", pk=order.pk)

    messages.success(request, "Маршрут утвержден, рейс создан.")
    return redirect("trips:detail", pk=trip.pk)


@manager_required
@require_GET
def trip_list(request):
    trips = _manager_trips_queryset(request)
    return render(request, "trips/trip_list.html", {"trips": trips})


@manager_required
@require_GET
def trip_detail(request, pk):
    trip = get_object_or_404(_manager_trips_queryset(request), pk=pk)
    status_events = trip.status_events.all().order_by("changed_at")
    return render(
        request,
        "trips/trip_detail.html",
        {
            "trip": trip,
            "status_events": status_events,
        },
    )


@manager_required
@require_POST
def trip_start(request, pk):
    trip = get_object_or_404(_manager_trips_queryset(request), pk=pk)
    try:
        TripLifecycleService().start_trip(trip, request.user)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("trips:detail", pk=trip.pk)

    messages.success(request, "Рейс начат.")
    return redirect("trips:detail", pk=trip.pk)


@manager_required
@require_POST
def trip_deliver(request, pk):
    trip = get_object_or_404(_manager_trips_queryset(request), pk=pk)
    try:
        TripLifecycleService().deliver_trip(trip, request.user)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("trips:detail", pk=trip.pk)

    messages.success(request, "Рейс завершен.")
    return redirect("trips:detail", pk=trip.pk)
