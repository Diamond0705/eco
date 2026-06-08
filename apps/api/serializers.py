from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
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
from apps.routing.views import (
    _calculation_details,
    _calculation_warnings,
    _has_unpriced_tolls,
    _route_option_rows,
)
from apps.trips.models import Trip


class UserSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    full_name = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.STR)
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


class ShipmentOrderWriteSerializer(serializers.Serializer):
    transport = serializers.PrimaryKeyRelatedField(
        queryset=Transport.objects.filter(is_active=True).select_related("eco_standard")
    )
    cargo_name = serializers.CharField(max_length=150)
    cargo_type = serializers.CharField(max_length=120)
    cargo_weight_kg = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    delivery_date = serializers.DateField()
    notes = serializers.CharField(required=False, allow_blank=True)
    origin_location = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.filter(is_active=True)
    )
    destination_location = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.filter(is_active=True)
    )

    def validate(self, attrs):
        transport = attrs.get("transport") or getattr(self.instance, "transport", None)
        cargo_weight_kg = attrs.get("cargo_weight_kg") or getattr(
            self.instance,
            "cargo_weight_kg",
            None,
        )
        delivery_date = attrs.get("delivery_date") or getattr(
            self.instance,
            "desired_delivery_date",
            None,
        )
        origin_location, destination_location = self._locations_for_validation(attrs)
        errors = {}

        if self.instance and self.instance.status != ShipmentOrder.Status.NEW:
            errors["status"] = "Заявку можно редактировать только в статусе new."
        if delivery_date and delivery_date < timezone.localdate():
            errors["delivery_date"] = "Желаемая дата доставки не может быть в прошлом."
        if transport and cargo_weight_kg and cargo_weight_kg > Decimal(transport.capacity_kg):
            errors["cargo_weight_kg"] = "Вес груза превышает грузоподъемность транспорта."
        if origin_location and destination_location and origin_location == destination_location:
            errors["destination_location"] = "Точки отправления и доставки должны различаться."
        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        origin_location = validated_data.pop("origin_location")
        destination_location = validated_data.pop("destination_location")
        delivery_date = validated_data.pop("delivery_date")
        with transaction.atomic():
            order = ShipmentOrder(
                manager=user,
                desired_delivery_date=delivery_date,
                status=ShipmentOrder.Status.NEW,
                **validated_data,
            )
            order.full_clean()
            order.save()
            self._save_points(order, origin_location, destination_location)
        return order

    def update(self, instance, validated_data):
        origin_location, destination_location = self._locations_for_update(validated_data)
        delivery_date = validated_data.pop("delivery_date", None)
        validated_data.pop("origin_location", None)
        validated_data.pop("destination_location", None)
        with transaction.atomic():
            for field, value in validated_data.items():
                setattr(instance, field, value)
            if delivery_date is not None:
                instance.desired_delivery_date = delivery_date
            instance.full_clean()
            instance.save()
            self._save_points(instance, origin_location, destination_location)
        return instance

    def _locations_for_validation(self, attrs):
        if not self.instance:
            return attrs.get("origin_location"), attrs.get("destination_location")
        return self._locations_for_update(attrs)

    def _locations_for_update(self, attrs):
        current_points = {
            point.sequence: point.location
            for point in self.instance.points.all().order_by("sequence")
        }
        return (
            attrs.get("origin_location") or current_points.get(1),
            attrs.get("destination_location") or current_points.get(2),
        )

    def _save_points(self, order, origin_location, destination_location):
        origin_point, _created = OrderPoint.objects.update_or_create(
            order=order,
            sequence=1,
            defaults={
                "location": origin_location,
                "point_type": OrderPoint.PointType.PICKUP,
            },
        )
        destination_point, _created = OrderPoint.objects.update_or_create(
            order=order,
            sequence=2,
            defaults={
                "location": destination_location,
                "point_type": OrderPoint.PointType.DELIVERY,
            },
        )
        order.points.exclude(pk__in=[origin_point.pk, destination_point.pk]).delete()


class RouteOptionSummarySerializer(serializers.ModelSerializer):
    co2_kg_per_km = serializers.SerializerMethodField()
    co2_kg_per_ton_km = serializers.SerializerMethodField()
    provider_display = serializers.CharField(source="get_provider_display", read_only=True)
    geometry_json = serializers.JSONField(read_only=True)

    class Meta:
        model = RouteOption
        fields = (
            "id",
            "name",
            "provider",
            "provider_display",
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
            "geometry_json",
        )

    @extend_schema_field(OpenApiTypes.STR)
    def get_co2_kg_per_km(self, route):
        return display_decimal(co2_kg_per_km(route), "0.001")

    @extend_schema_field(OpenApiTypes.STR)
    def get_co2_kg_per_ton_km(self, route):
        return display_decimal(co2_kg_per_ton_km(route), "0.0001")


class RouteOptionDetailSerializer(RouteOptionSummarySerializer):
    display_name = serializers.SerializerMethodField()
    badges = serializers.SerializerMethodField()
    calculation_details = serializers.SerializerMethodField()
    warnings = serializers.SerializerMethodField()
    has_unpriced_tolls = serializers.SerializerMethodField()

    class Meta(RouteOptionSummarySerializer.Meta):
        fields = RouteOptionSummarySerializer.Meta.fields + (
            "display_name",
            "badges",
            "calculation_details",
            "warnings",
            "has_unpriced_tolls",
        )

    @extend_schema_field(OpenApiTypes.STR)
    def get_display_name(self, route):
        row = self._row_for_route(route)
        if row:
            return row["display_name"]
        return route.name

    @extend_schema_field(list[str])
    def get_badges(self, route):
        row = self._row_for_route(route)
        return row["badges"] if row else []

    @extend_schema_field(dict[str, OpenApiTypes.STR])
    def get_calculation_details(self, route):
        return _calculation_details(route)

    @extend_schema_field(list[str])
    def get_warnings(self, route):
        return _calculation_warnings(route)

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_has_unpriced_tolls(self, route):
        return _has_unpriced_tolls(route)

    def _row_for_route(self, route):
        rows_by_id = self.context.get("route_rows_by_id")
        if rows_by_id is None:
            rows = _route_option_rows(list(route.order.route_options.all().order_by("created_at")))
            rows_by_id = {row["option"].pk: row for row in rows}
            self.context["route_rows_by_id"] = rows_by_id
        return rows_by_id.get(route.pk)


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
            "notes",
            "created_at",
            "updated_at",
        )


class OrderDetailSerializer(OrderListSerializer):
    points = OrderPointSerializer(many=True, read_only=True)
    route_options = RouteOptionDetailSerializer(many=True, read_only=True)

    class Meta(OrderListSerializer.Meta):
        fields = OrderListSerializer.Meta.fields + ("points", "route_options")


class TripStatusEventSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    old_status = serializers.CharField()
    new_status = serializers.CharField()
    changed_at = serializers.DateTimeField()
    event_at = serializers.DateTimeField(allow_null=True)
    comment = serializers.CharField()
    changed_by = UserSummarySerializer(read_only=True)


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

    @extend_schema_field(UserSummarySerializer)
    def get_manager(self, trip):
        return UserSummarySerializer(trip.order.manager).data

    @extend_schema_field(TransportSummarySerializer)
    def get_transport(self, trip):
        return TransportSummarySerializer(trip.order.transport).data

    @extend_schema_field(OpenApiTypes.DATETIME)
    def get_planned_finish(self, trip):
        return None


class TripDetailSerializer(TripSerializer):
    status_events = TripStatusEventSerializer(many=True, read_only=True)

    class Meta(TripSerializer.Meta):
        fields = TripSerializer.Meta.fields + ("status_events",)


class TripStartSerializer(serializers.Serializer):
    actual_start = serializers.DateTimeField(required=False, allow_null=True)
    comment = serializers.CharField(required=False, allow_blank=True)


class TripDeliverSerializer(serializers.Serializer):
    actual_finish = serializers.DateTimeField(required=False, allow_null=True)
    comment = serializers.CharField(required=False, allow_blank=True)


class ManagerDashboardSerializer(serializers.Serializer):
    orders = serializers.DictField()
    trips = serializers.DictField()
    delivered = serializers.DictField()
    recent_delivered_trips = TripSerializer(many=True)


class EmissionsReportRowSerializer(serializers.Serializer):
    trip_id = serializers.IntegerField(source="trip.pk")
    finish_date = serializers.DateTimeField()
    cargo = serializers.CharField()
    transport = serializers.CharField()
    euro_class = serializers.CharField()
    route_name = serializers.CharField()
    distance_km = serializers.DecimalField(max_digits=10, decimal_places=2)
    fuel_liters = serializers.DecimalField(max_digits=10, decimal_places=2)
    cost_rub = serializers.DecimalField(max_digits=12, decimal_places=2)
    co2_kg = serializers.DecimalField(max_digits=10, decimal_places=2)
    nox_g = serializers.DecimalField(max_digits=10, decimal_places=2)
    pm_g = serializers.DecimalField(max_digits=10, decimal_places=3)
    eco_rating = serializers.DecimalField(max_digits=5, decimal_places=2)
    co2_kg_per_km = serializers.CharField()
    co2_kg_per_ton_km = serializers.CharField()
    has_tolls = serializers.BooleanField()


class EmissionsReportSerializer(serializers.Serializer):
    filters = serializers.DictField()
    summary = serializers.DictField()
    rows = EmissionsReportRowSerializer(many=True)


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
