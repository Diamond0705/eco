from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.fleet.models import EcoStandard, Transport
from apps.locations.models import Location
from apps.orders.models import ShipmentOrder
from apps.routing.services.route_calculation_service import RouteCalculationService
from apps.trips.models import Trip, TripStatusEvent
from apps.trips.services import TripLifecycleService
from tests.test_routing_views import create_order

User = get_user_model()


@pytest.fixture
def manager():
    return User.objects.create_user(
        username="trip_view_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )


@pytest.fixture
def other_manager():
    return User.objects.create_user(
        username="trip_view_other_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        username="trip_view_admin",
        password="StrongPass12345",
        role=User.Role.ADMIN,
    )


@pytest.fixture
def superuser():
    return User.objects.create_superuser(
        username="trip_view_superuser",
        email="trip_view_superuser@example.com",
        password="StrongPass12345",
    )


@pytest.fixture
def calculated_order(manager, transport, locations):
    order = create_order(manager, transport, locations)
    RouteCalculationService().calculate_for_order(order)
    order.refresh_from_db()
    return order


@pytest.fixture
def transport():
    standard = EcoStandard.objects.create(
        name="Euro VI",
        nox_limit_g_per_kwh=Decimal("0.46"),
        pm_limit_mg_per_kwh=Decimal("10.00"),
    )
    return Transport.objects.create(
        plate_number="Р600РР777",
        model="КАМАЗ 5490",
        category=Transport.Category.N3,
        capacity_kg=20000,
        fuel_consumption_l_per_100km=Decimal("29.00"),
        eco_standard=standard,
        year=2021,
    )


@pytest.fixture
def locations():
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
    return origin, destination


@pytest.mark.django_db
def test_manager_can_approve_route_for_own_order(client, manager, calculated_order):
    route = calculated_order.route_options.first()
    client.force_login(manager)

    response = client.post(
        reverse(
            "trips:approve_route",
            kwargs={"order_id": calculated_order.pk, "route_option_id": route.pk},
        )
    )
    calculated_order.refresh_from_db()
    route.refresh_from_db()

    trip = Trip.objects.get(order=calculated_order)
    assert response.status_code == 302
    assert response["Location"] == reverse("trips:detail", kwargs={"pk": trip.pk})
    assert route.is_selected is True
    assert calculated_order.status == ShipmentOrder.Status.PLANNED


@pytest.mark.django_db
def test_get_approve_does_not_approve(client, manager, calculated_order):
    route = calculated_order.route_options.first()
    client.force_login(manager)

    response = client.get(
        reverse(
            "trips:approve_route",
            kwargs={"order_id": calculated_order.pk, "route_option_id": route.pk},
        )
    )

    assert response.status_code == 405
    assert Trip.objects.count() == 0


@pytest.mark.django_db
def test_approving_twice_redirects_to_existing_trip(client, manager, calculated_order):
    route = calculated_order.route_options.first()
    trip = TripLifecycleService().approve_route(calculated_order, route, manager)
    client.force_login(manager)

    response = client.post(
        reverse(
            "trips:approve_route",
            kwargs={"order_id": calculated_order.pk, "route_option_id": route.pk},
        )
    )

    assert response.status_code == 302
    assert response["Location"] == reverse("trips:detail", kwargs={"pk": trip.pk})
    assert Trip.objects.filter(order=calculated_order).count() == 1


@pytest.mark.django_db
def test_manager_cannot_approve_another_manager_route(
    client, manager, other_manager, transport, locations
):
    order = create_order(other_manager, transport, locations)
    RouteCalculationService().calculate_for_order(order)
    route = order.route_options.first()
    client.force_login(manager)

    response = client.post(
        reverse(
            "trips:approve_route",
            kwargs={"order_id": order.pk, "route_option_id": route.pk},
        )
    )

    assert response.status_code == 404
    assert Trip.objects.count() == 0


@pytest.mark.django_db
def test_anonymous_redirected_and_admin_gets_403_for_trip_actions(
    client, manager, admin_user, superuser, calculated_order
):
    route = calculated_order.route_options.first()
    approve_url = reverse(
        "trips:approve_route",
        kwargs={"order_id": calculated_order.pk, "route_option_id": route.pk},
    )
    assert client.post(approve_url).status_code == 302

    for user in (admin_user, superuser):
        client.force_login(user)
        assert client.post(approve_url).status_code == 403
        assert client.get(reverse("trips:list")).status_code == 403


@pytest.mark.django_db
def test_trip_list_shows_only_current_manager_trips(
    client, manager, other_manager, calculated_order, transport, locations
):
    own_trip = TripLifecycleService().approve_route(
        calculated_order,
        calculated_order.route_options.first(),
        manager,
    )
    other_order = create_order(other_manager, transport, locations)
    other_order.cargo_name = "Чужой груз"
    other_order.save(update_fields=["cargo_name", "updated_at"])
    RouteCalculationService().calculate_for_order(other_order)
    other_trip = TripLifecycleService().approve_route(
        other_order,
        other_order.route_options.first(),
        other_manager,
    )
    client.force_login(manager)

    response = client.get(reverse("trips:list"))
    content = response.content.decode()

    assert response.status_code == 200
    assert f"№{own_trip.id}" in content
    assert f"№{other_trip.id}" not in content
    assert "Чужой груз" not in content


@pytest.mark.django_db
def test_trip_detail_for_another_manager_returns_404(
    client, manager, other_manager, transport, locations
):
    other_order = create_order(other_manager, transport, locations)
    RouteCalculationService().calculate_for_order(other_order)
    trip = TripLifecycleService().approve_route(
        other_order,
        other_order.route_options.first(),
        other_manager,
    )
    client.force_login(manager)

    response = client.get(reverse("trips:detail", kwargs={"pk": trip.pk}))

    assert response.status_code == 404


@pytest.mark.django_db
def test_start_and_deliver_actions_are_post_only(client, manager, calculated_order):
    trip = TripLifecycleService().approve_route(
        calculated_order,
        calculated_order.route_options.first(),
        manager,
    )
    client.force_login(manager)

    assert client.get(reverse("trips:start", kwargs={"pk": trip.pk})).status_code == 405
    trip.refresh_from_db()
    assert trip.status == Trip.Status.PLANNED

    assert client.post(reverse("trips:start", kwargs={"pk": trip.pk})).status_code == 302
    trip.refresh_from_db()
    assert trip.status == Trip.Status.IN_PROGRESS

    assert client.get(reverse("trips:deliver", kwargs={"pk": trip.pk})).status_code == 405
    trip.refresh_from_db()
    assert trip.status == Trip.Status.IN_PROGRESS


@pytest.mark.django_db
def test_deliver_action_updates_order_and_creates_event(client, manager, calculated_order):
    trip = TripLifecycleService().approve_route(
        calculated_order,
        calculated_order.route_options.first(),
        manager,
    )
    TripLifecycleService().start_trip(trip, manager)
    client.force_login(manager)

    response = client.post(reverse("trips:deliver", kwargs={"pk": trip.pk}))
    trip.refresh_from_db()
    calculated_order.refresh_from_db()

    assert response.status_code == 302
    assert trip.status == Trip.Status.DELIVERED
    assert trip.actual_finish_at is not None
    assert calculated_order.status == ShipmentOrder.Status.COMPLETED
    assert TripStatusEvent.objects.filter(trip=trip, new_status=Trip.Status.DELIVERED).exists()


@pytest.mark.django_db
def test_trip_detail_displays_metrics_history_and_pdf_placeholder(
    client, manager, calculated_order
):
    trip = TripLifecycleService().approve_route(
        calculated_order,
        calculated_order.route_options.first(),
        manager,
    )
    client.force_login(manager)

    response = client.get(reverse("trips:detail", kwargs={"pk": trip.pk}))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Стоимость" in content
    assert "История статусов" in content
    assert "PDF-путевой лист будет добавлен на следующем этапе." in content
    assert not trip.waybill_pdf
