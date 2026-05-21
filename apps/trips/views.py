from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from apps.core.permissions import manager_required
from apps.orders.models import ShipmentOrder
from apps.routing.models import RouteOption

from .forms import TripDeliverForm, TripStartForm, datetime_local_initial
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
        .prefetch_related("order__points__location", "status_events__changed_by")
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
    selected_status = request.GET.get("status", "")
    valid_statuses = {choice.value for choice in Trip.Status}
    if selected_status in valid_statuses:
        trips = trips.filter(status=selected_status)
    else:
        selected_status = ""
    trips = list(trips)
    _attach_route_display_names(trips)

    return render(
        request,
        "trips/trip_list.html",
        {
            "trips": trips,
            "status_choices": Trip.Status.choices,
            "selected_status": selected_status,
        },
    )


@manager_required
@require_GET
def trip_detail(request, pk):
    trip = get_object_or_404(_manager_trips_queryset(request), pk=pk)
    _attach_route_display_names([trip])
    status_events = trip.status_events.all().order_by("changed_at")
    start_form = None
    deliver_form = None
    if trip.status == Trip.Status.PLANNED:
        start_form = TripStartForm(initial={"actual_start_at": datetime_local_initial()})
    if trip.status == Trip.Status.IN_PROGRESS:
        deliver_form = TripDeliverForm(initial={"actual_finish_at": datetime_local_initial()})
    return render(
        request,
        "trips/trip_detail.html",
        {
            "trip": trip,
            "status_events": status_events,
            "start_form": start_form,
            "deliver_form": deliver_form,
        },
    )


@manager_required
@require_POST
def trip_start(request, pk):
    trip = get_object_or_404(_manager_trips_queryset(request), pk=pk)
    form = TripStartForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Проверьте фактическое время начала рейса.")
        return redirect("trips:detail", pk=trip.pk)

    try:
        TripLifecycleService().start_trip(
            trip,
            request.user,
            actual_start_at=form.cleaned_data["actual_start_at"],
            comment=form.cleaned_data["comment"],
        )
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("trips:detail", pk=trip.pk)

    messages.success(request, "Рейс начат.")
    return redirect("trips:detail", pk=trip.pk)


def _attach_route_display_names(trips):
    for trip in trips:
        points = sorted(trip.order.points.all(), key=lambda point: point.sequence)
        if len(points) >= 2:
            trip.display_route_name = f"{points[0].location.name} — {points[-1].location.name}"
        else:
            trip.display_route_name = trip.route_option.name


@manager_required
@require_POST
def trip_deliver(request, pk):
    trip = get_object_or_404(_manager_trips_queryset(request), pk=pk)
    form = TripDeliverForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Проверьте фактическое время завершения рейса.")
        return redirect("trips:detail", pk=trip.pk)

    try:
        TripLifecycleService().deliver_trip(
            trip,
            request.user,
            actual_finish_at=form.cleaned_data["actual_finish_at"],
            comment=form.cleaned_data["comment"],
        )
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("trips:detail", pk=trip.pk)

    messages.success(request, "Рейс завершен.")
    return redirect("trips:detail", pk=trip.pk)
