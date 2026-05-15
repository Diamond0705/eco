from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.fleet.models import EcoStandard, Transport
from apps.locations.models import Location
from apps.orders.models import OrderPoint, ShipmentOrder
from apps.routing.models import RouteOption
from apps.routing.services.route_calculation_service import RouteCalculationService
from apps.trips.models import Trip, TripStatusEvent
from apps.trips.services import TripLifecycleService

User = get_user_model()


@pytest.fixture
def manager():
    return User.objects.create_user(
        username="trip_service_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )


@pytest.fixture
def other_manager():
    return User.objects.create_user(
        username="trip_service_other_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )


@pytest.fixture
def order_with_routes(manager):
    standard = EcoStandard.objects.create(
        name="Euro VI",
        nox_limit_g_per_kwh=Decimal("0.46"),
        pm_limit_mg_per_kwh=Decimal("10.00"),
    )
    transport = Transport.objects.create(
        plate_number="Р500РР777",
        model="КАМАЗ 5490",
        category=Transport.Category.N3,
        capacity_kg=20000,
        fuel_consumption_l_per_100km=Decimal("29.00"),
        eco_standard=standard,
        year=2021,
    )
    origin = Location.objects.create(
        name="Москва",
        latitude=Decimal("55.7558"),
        longitude=Decimal("37.6173"),
    )
    destination = Location.objects.create(
        name="Подольск",
        latitude=Decimal("55.4312"),
        longitude=Decimal("37.5447"),
    )
    order = ShipmentOrder.objects.create(
        manager=manager,
        transport=transport,
        cargo_name="Оборудование",
        cargo_type="Паллеты",
        cargo_weight_kg=Decimal("1000.00"),
        desired_delivery_date="2026-06-01",
    )
    OrderPoint.objects.create(
        order=order,
        location=origin,
        sequence=1,
        point_type=OrderPoint.PointType.PICKUP,
    )
    OrderPoint.objects.create(
        order=order,
        location=destination,
        sequence=2,
        point_type=OrderPoint.PointType.DELIVERY,
    )
    RouteCalculationService().calculate_for_order(order)
    order.refresh_from_db()
    return order


@pytest.mark.django_db
def test_approving_route_creates_trip_and_status_event(order_with_routes, manager):
    route = order_with_routes.route_options.first()

    trip = TripLifecycleService().approve_route(order_with_routes, route, manager)
    order_with_routes.refresh_from_db()
    route.refresh_from_db()

    assert trip.order == order_with_routes
    assert trip.route_option == route
    assert trip.status == Trip.Status.PLANNED
    assert route.is_selected is True
    assert order_with_routes.status == ShipmentOrder.Status.PLANNED
    assert TripStatusEvent.objects.filter(
        trip=trip,
        old_status="",
        new_status=Trip.Status.PLANNED,
        changed_by=manager,
    ).exists()


@pytest.mark.django_db
def test_approving_route_unselects_other_route_options(order_with_routes, manager):
    routes = list(order_with_routes.route_options.order_by("id"))
    routes[1].is_selected = True
    routes[1].save(update_fields=["is_selected"])

    TripLifecycleService().approve_route(order_with_routes, routes[0], manager)

    selected_values = list(
        RouteOption.objects.filter(order=order_with_routes).order_by("id").values_list(
            "is_selected",
            flat=True,
        )
    )
    assert selected_values == [True, False, False]


@pytest.mark.django_db
def test_approving_route_twice_does_not_create_duplicate_trips(order_with_routes, manager):
    route = order_with_routes.route_options.first()
    TripLifecycleService().approve_route(order_with_routes, route, manager)

    with pytest.raises(ValueError):
        TripLifecycleService().approve_route(order_with_routes, route, manager)

    assert Trip.objects.filter(order=order_with_routes).count() == 1


@pytest.mark.django_db
def test_manager_cannot_approve_another_manager_route(
    order_with_routes, manager, other_manager
):
    route = order_with_routes.route_options.first()

    with pytest.raises(ValueError):
        TripLifecycleService().approve_route(order_with_routes, route, other_manager)

    assert Trip.objects.count() == 0


@pytest.mark.django_db
def test_trip_start_and_deliver_transitions_create_events(order_with_routes, manager):
    route = order_with_routes.route_options.first()
    trip = TripLifecycleService().approve_route(order_with_routes, route, manager)

    TripLifecycleService().start_trip(trip, manager)
    trip.refresh_from_db()
    assert trip.status == Trip.Status.IN_PROGRESS
    assert trip.actual_start_at is not None

    TripLifecycleService().deliver_trip(trip, manager)
    trip.refresh_from_db()
    order_with_routes.refresh_from_db()

    assert trip.status == Trip.Status.DELIVERED
    assert trip.actual_finish_at is not None
    assert order_with_routes.status == ShipmentOrder.Status.COMPLETED
    assert trip.status_events.filter(new_status=Trip.Status.IN_PROGRESS).exists()
    assert trip.status_events.filter(new_status=Trip.Status.DELIVERED).exists()


@pytest.mark.django_db
def test_delivered_trip_cannot_be_changed(order_with_routes, manager):
    route = order_with_routes.route_options.first()
    trip = TripLifecycleService().approve_route(order_with_routes, route, manager)
    TripLifecycleService().start_trip(trip, manager)
    TripLifecycleService().deliver_trip(trip, manager)

    with pytest.raises(ValueError):
        TripLifecycleService().start_trip(trip, manager)
