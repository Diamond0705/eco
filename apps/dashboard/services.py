from dataclasses import dataclass
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone

from apps.fleet.models import Transport
from apps.orders.models import ShipmentOrder
from apps.routing.services.route_snapshot_metrics import (
    average_decimal,
    co2_kg_per_km,
    co2_kg_per_ton_km,
    display_decimal,
    has_tolls,
)
from apps.trips.display import attach_route_display_names
from apps.trips.models import Trip


@dataclass(frozen=True)
class AnalyticsFilters:
    date_from: object = None
    date_to: object = None
    error_message: str = ""


class AnalyticsFilterParser:
    def parse(self, query_params):
        date_from = self._parse_date(query_params.get("date_from", "").strip())
        date_to = self._parse_date(query_params.get("date_to", "").strip())
        error_message = ""

        if query_params.get("date_from", "").strip() and date_from is None:
            error_message = "Некорректная дата начала периода."
        if query_params.get("date_to", "").strip() and date_to is None:
            error_message = "Некорректная дата окончания периода."

        return AnalyticsFilters(date_from=date_from, date_to=date_to, error_message=error_message)

    def _parse_date(self, value):
        if not value:
            return None
        try:
            return timezone.datetime.fromisoformat(value).date()
        except ValueError:
            return None


class ManagerAnalyticsService:
    def build(self, manager, filters=None):
        filters = filters or AnalyticsFilters()
        orders = ShipmentOrder.objects.filter(manager=manager)
        trips = Trip.objects.filter(order__manager=manager)
        delivered_trips = self._filtered_delivered_trips(
            trips.filter(status=Trip.Status.DELIVERED), filters
        )

        delivered_rows = list(
            delivered_trips.select_related("order", "order__transport", "route_option")
            .prefetch_related("order__points__location")
            .order_by("-actual_finish_at", "-created_at")
        )
        attach_route_display_names(delivered_rows)

        return {
            "filters": filters,
            "orders": {
                "total": orders.count(),
                "by_status": self._count_orders_by_status(orders),
            },
            "trips": {
                "total": trips.count(),
                "planned": trips.filter(status=Trip.Status.PLANNED).count(),
                "in_progress": trips.filter(status=Trip.Status.IN_PROGRESS).count(),
                "delivered": trips.filter(status=Trip.Status.DELIVERED).count(),
                "active": trips.filter(
                    status__in=[Trip.Status.PLANNED, Trip.Status.IN_PROGRESS]
                ).count(),
            },
            "delivered": self._summary(delivered_rows),
            "recent_delivered_trips": delivered_rows[:10],
        }

    def _filtered_delivered_trips(self, queryset, filters):
        if filters.date_from:
            queryset = queryset.filter(actual_finish_at__date__gte=filters.date_from)
        if filters.date_to:
            queryset = queryset.filter(actual_finish_at__date__lte=filters.date_to)
        return queryset

    def _count_orders_by_status(self, orders):
        counts = dict(orders.values_list("status").annotate(total=Count("id")))
        return {
            status.value: counts.get(status.value, 0)
            for status in ShipmentOrder.Status
        }

    def _summary(self, trips):
        summary = {
            "trips_count": len(trips),
            "distance_km": sum((trip.route_option.distance_km for trip in trips), Decimal("0.00")),
            "fuel_liters": sum(
                (trip.route_option.fuel_liters for trip in trips), Decimal("0.00")
            ),
            "cost_rub": sum((trip.route_option.cost_rub for trip in trips), Decimal("0.00")),
            "co2_kg": sum((trip.route_option.co2_kg for trip in trips), Decimal("0.00")),
            "nox_g": sum((trip.route_option.nox_g for trip in trips), Decimal("0.00")),
            "pm_g": sum((trip.route_option.pm_g for trip in trips), Decimal("0.000")),
            "average_eco_rating": Decimal("0.00"),
            "average_co2_kg_per_km": "—",
            "average_co2_kg_per_ton_km": "—",
            "toll_routes_count": sum(1 for trip in trips if has_tolls(trip.route_option)),
        }
        if trips:
            summary["average_eco_rating"] = (
                sum((trip.route_option.eco_rating for trip in trips), Decimal("0.00"))
                / Decimal(len(trips))
            ).quantize(Decimal("0.01"))
            summary["average_co2_kg_per_km"] = display_decimal(
                average_decimal(
                    (co2_kg_per_km(trip.route_option) for trip in trips),
                    "0.001",
                ),
                "0.001",
            )
            summary["average_co2_kg_per_ton_km"] = display_decimal(
                average_decimal(
                    (co2_kg_per_ton_km(trip.route_option) for trip in trips),
                    "0.0001",
                ),
                "0.0001",
            )
        return summary


class AdminDashboardService:
    def build(self):
        user_model = get_user_model()
        users = user_model.objects.all()
        orders = ShipmentOrder.objects.all()
        trips = Trip.objects.select_related(
            "order",
            "order__manager",
            "order__transport",
            "order__transport__eco_standard",
            "route_option",
        ).prefetch_related("order__points__location")
        delivered_trips = list(trips.filter(status=Trip.Status.DELIVERED))
        attach_route_display_names(delivered_trips)
        recent_trips = list(trips.order_by("-created_at")[:10])
        attach_route_display_names(recent_trips)

        return {
            "users": {
                "total": users.count(),
                "managers": users.filter(role="manager", is_superuser=False).count(),
            },
            "transports": {
                "total": Transport.objects.count(),
            },
            "orders": {
                "total": orders.count(),
            },
            "trips": {
                "total": trips.count(),
                "delivered": trips.filter(status=Trip.Status.DELIVERED).count(),
            },
            "company": ManagerAnalyticsService()._summary(delivered_trips),
            "top_managers": self._top_managers(),
            "top_transports": self._top_transports(),
            "delivered_trips": delivered_trips,
            "recent_trips": recent_trips,
        }

    def _top_managers(self):
        return (
            Trip.objects.filter(status=Trip.Status.DELIVERED)
            .values(
                "order__manager__username",
                "order__manager__first_name",
                "order__manager__last_name",
            )
            .annotate(delivered_count=Count("id"))
            .order_by("-delivered_count", "order__manager__username")[:5]
        )

    def _top_transports(self):
        return (
            Trip.objects.filter(status=Trip.Status.DELIVERED)
            .values("order__transport__plate_number", "order__transport__model")
            .annotate(delivered_count=Count("id"))
            .order_by("-delivered_count", "order__transport__plate_number")[:5]
        )
