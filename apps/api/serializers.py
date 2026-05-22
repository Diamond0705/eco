from decimal import Decimal

from rest_framework import serializers

from apps.fleet.models import Transport
from apps.locations.models import Location
from apps.orders.models import OrderPoint, ShipmentOrder
from apps.routing.models import RouteOption
from apps.routing.services.route_snapshot_metrics import (
    average_decimal,
    co2_kg_per_km,
    co2_kg_per_ton_km,
    display_decimal,
)
from apps.trips.models import Trip


class UserSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    full_name = serializers.SerializerMethodField()

    def get_full_name(self, user):
        return user.get_full_name()


class CurrentUserSerializer(UserSummarySerializer):
    role = serializers.CharField()


class EcoStandardSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class TransportSummarySerializer(serializers.ModelSerializer):
    eco_standard = EcoStandardSummarySerializer(read_only=True)

    class Meta:
        model = Transport
        fields = (
            "id",
            "plate_number",
            "model",
            "category",
            "fuel_type",
            "capacity_kg",
            "fuel_consumption_l_per_100km",
            "eco_standard",
            "is_active",
        )


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ("id", "name", "address", "latitude", "longitude", "is_active")


class OrderPointSerializer(serializers.ModelSerializer):
    location = LocationSerializer(read_only=True)

    class Meta:
        model = OrderPoint
        fields = ("id", "sequence", "point_type", "location")


class RouteOptionSummarySerializer(serializers.ModelSerializer):
    co2_kg_per_km = serializers.SerializerMethodField()
    co2_kg_per_ton_km = serializers.SerializerMethodField()

    class Meta:
        model = RouteOption
        fields = (
            "id",
            "name",
            "is_selected",
            "distance_km",
            "duration_minutes",
            "fuel_liters",
            "cost_rub",
            "co2_kg",
            "nox_g",
            "pm_g",
            "eco_rating",
            "calculation_model_version",
            "co2_kg_per_km",
            "co2_kg_per_ton_km",
        )

    def get_co2_kg_per_km(self, route):
        return display_decimal(co2_kg_per_km(route), "0.001")

    def get_co2_kg_per_ton_km(self, route):
        return display_decimal(co2_kg_per_ton_km(route), "0.0001")


class OrderListSerializer(serializers.ModelSerializer):
    manager = UserSummarySerializer(read_only=True)
    transport = TransportSummarySerializer(read_only=True)
    delivery_date = serializers.DateField(source="desired_delivery_date")

    class Meta:
        model = ShipmentOrder
        fields = (
            "id",
            "manager",
            "cargo_name",
            "cargo_type",
            "cargo_weight_kg",
            "status",
            "transport",
            "delivery_date",
            "created_at",
            "updated_at",
        )


class OrderDetailSerializer(OrderListSerializer):
    points = OrderPointSerializer(many=True, read_only=True)
    route_options = RouteOptionSummarySerializer(many=True, read_only=True)

    class Meta(OrderListSerializer.Meta):
        fields = OrderListSerializer.Meta.fields + ("points", "route_options")


class TripSerializer(serializers.ModelSerializer):
    order = OrderListSerializer(read_only=True)
    manager = serializers.SerializerMethodField()
    transport = serializers.SerializerMethodField()
    planned_start = serializers.DateTimeField(source="planned_start_at")
    planned_finish = serializers.SerializerMethodField()
    actual_start = serializers.DateTimeField(source="actual_start_at")
    actual_finish = serializers.DateTimeField(source="actual_finish_at")
    route_option = RouteOptionSummarySerializer(read_only=True)

    class Meta:
        model = Trip
        fields = (
            "id",
            "order",
            "manager",
            "transport",
            "status",
            "planned_start",
            "planned_finish",
            "actual_start",
            "actual_finish",
            "route_option",
        )

    def get_manager(self, trip):
        return UserSummarySerializer(trip.order.manager).data

    def get_transport(self, trip):
        return TransportSummarySerializer(trip.order.transport).data

    def get_planned_finish(self, trip):
        return None


class AnalyticsSummarySerializer(serializers.Serializer):
    delivered_trips_count = serializers.IntegerField()
    total_distance_km = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_cost_rub = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_co2_kg = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_nox_g = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_pm_g = serializers.DecimalField(max_digits=12, decimal_places=3)
    average_eco_rating = serializers.DecimalField(max_digits=6, decimal_places=2)
    average_co2_kg_per_km = serializers.CharField()
    average_co2_kg_per_ton_km = serializers.CharField()


def build_analytics_summary(trips):
    trips = list(trips)
    return {
        "delivered_trips_count": len(trips),
        "total_distance_km": sum(
            (trip.route_option.distance_km for trip in trips),
            Decimal("0.00"),
        ),
        "total_cost_rub": sum((trip.route_option.cost_rub for trip in trips), Decimal("0.00")),
        "total_co2_kg": sum((trip.route_option.co2_kg for trip in trips), Decimal("0.00")),
        "total_nox_g": sum((trip.route_option.nox_g for trip in trips), Decimal("0.00")),
        "total_pm_g": sum((trip.route_option.pm_g for trip in trips), Decimal("0.000")),
        "average_eco_rating": average_decimal(
            (trip.route_option.eco_rating for trip in trips),
            "0.01",
        )
        or Decimal("0.00"),
        "average_co2_kg_per_km": display_decimal(
            average_decimal((co2_kg_per_km(trip.route_option) for trip in trips), "0.001"),
            "0.001",
        ),
        "average_co2_kg_per_ton_km": display_decimal(
            average_decimal(
                (co2_kg_per_ton_km(trip.route_option) for trip in trips),
                "0.0001",
            ),
            "0.0001",
        ),
    }
