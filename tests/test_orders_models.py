from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from apps.fleet.models import EcoStandard, Transport
from apps.locations.models import Location
from apps.orders.forms import ShipmentOrderCreateForm
from apps.orders.models import OrderPoint, ShipmentOrder

User = get_user_model()


@pytest.fixture
def manager():
    return User.objects.create_user(
        username="orders_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )


@pytest.fixture
def eco_standard():
    return EcoStandard.objects.create(
        name="Euro VI",
        nox_limit_g_per_kwh=Decimal("0.46"),
        pm_limit_mg_per_kwh=Decimal("10.00"),
    )


@pytest.fixture
def transport(eco_standard):
    return Transport.objects.create(
        plate_number="О111ОО777",
        model="КАМАЗ 5490",
        category=Transport.Category.N3,
        fuel_type=Transport.FuelType.DIESEL,
        capacity_kg=20000,
        fuel_consumption_l_per_100km=Decimal("29.00"),
        eco_standard=eco_standard,
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
def test_shipment_order_creation_with_two_points(manager, transport, locations):
    origin, destination = locations
    order = ShipmentOrder.objects.create(
        manager=manager,
        transport=transport,
        cargo_name="Оборудование",
        cargo_type="Паллеты",
        cargo_weight_kg=Decimal("1000.00"),
        desired_delivery_date=date(2026, 6, 1),
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

    assert str(order) == f"Заявка №{order.pk}: Оборудование"
    assert list(order.points.values_list("sequence", "point_type")) == [
        (1, OrderPoint.PointType.PICKUP),
        (2, OrderPoint.PointType.DELIVERY),
    ]


@pytest.mark.django_db
def test_cargo_weight_must_be_positive(manager, transport):
    order = ShipmentOrder(
        manager=manager,
        transport=transport,
        cargo_name="Оборудование",
        cargo_type="Паллеты",
        cargo_weight_kg=Decimal("0.00"),
        desired_delivery_date=date(2026, 6, 1),
    )

    with pytest.raises(ValidationError):
        order.full_clean()


@pytest.mark.django_db
def test_cargo_weight_must_not_exceed_transport_capacity(manager, transport):
    order = ShipmentOrder(
        manager=manager,
        transport=transport,
        cargo_name="Оборудование",
        cargo_type="Паллеты",
        cargo_weight_kg=Decimal("25000.00"),
        desired_delivery_date=date(2026, 6, 1),
    )

    with pytest.raises(ValidationError):
        order.full_clean()


@pytest.mark.django_db
def test_order_point_sequence_must_be_positive(manager, transport, locations):
    order = ShipmentOrder.objects.create(
        manager=manager,
        transport=transport,
        cargo_name="Оборудование",
        cargo_type="Паллеты",
        cargo_weight_kg=Decimal("1000.00"),
        desired_delivery_date=date(2026, 6, 1),
    )
    point = OrderPoint(
        order=order,
        location=locations[0],
        sequence=0,
        point_type=OrderPoint.PointType.PICKUP,
    )

    with pytest.raises(ValidationError):
        point.full_clean()


@pytest.mark.django_db
def test_order_point_sequence_is_unique_inside_order(manager, transport, locations):
    origin, destination = locations
    order = ShipmentOrder.objects.create(
        manager=manager,
        transport=transport,
        cargo_name="Оборудование",
        cargo_type="Паллеты",
        cargo_weight_kg=Decimal("1000.00"),
        desired_delivery_date=date(2026, 6, 1),
    )
    OrderPoint.objects.create(
        order=order,
        location=origin,
        sequence=1,
        point_type=OrderPoint.PointType.PICKUP,
    )

    with pytest.raises(IntegrityError):
        OrderPoint.objects.create(
            order=order,
            location=destination,
            sequence=1,
            point_type=OrderPoint.PointType.DELIVERY,
        )


@pytest.mark.django_db
def test_create_form_rejects_same_origin_and_destination(transport, locations):
    origin, _destination = locations
    form = ShipmentOrderCreateForm(
        data={
            "transport": transport.pk,
            "cargo_name": "Оборудование",
            "cargo_type": "Паллеты",
            "cargo_weight_kg": "1000.00",
            "desired_delivery_date": "2026-06-01",
            "origin_location": origin.pk,
            "destination_location": origin.pk,
        }
    )

    assert not form.is_valid()
    assert "Точка отправления и точка доставки должны различаться." in form.errors["__all__"]


@pytest.mark.django_db
def test_create_form_rejects_weight_above_capacity(transport, locations):
    origin, destination = locations
    form = ShipmentOrderCreateForm(
        data={
            "transport": transport.pk,
            "cargo_name": "Оборудование",
            "cargo_type": "Паллеты",
            "cargo_weight_kg": "25000.00",
            "desired_delivery_date": "2026-06-01",
            "origin_location": origin.pk,
            "destination_location": destination.pk,
        }
    )

    assert not form.is_valid()
    assert "Вес груза превышает грузоподъемность" in form.errors["cargo_weight_kg"][0]


@pytest.mark.django_db
def test_create_form_rejects_past_delivery_date(transport, locations):
    origin, destination = locations
    past_date = timezone.localdate() - timedelta(days=1)
    form = ShipmentOrderCreateForm(
        data={
            "transport": transport.pk,
            "cargo_name": "Оборудование",
            "cargo_type": "Паллеты",
            "cargo_weight_kg": "1000.00",
            "desired_delivery_date": past_date.isoformat(),
            "origin_location": origin.pk,
            "destination_location": destination.pk,
        }
    )

    assert not form.is_valid()
    assert "Желаемая дата доставки не может быть в прошлом." in form.errors[
        "desired_delivery_date"
    ]


@pytest.mark.django_db
@pytest.mark.parametrize("day_offset", [0, 1])
def test_create_form_accepts_today_and_future_delivery_dates(transport, locations, day_offset):
    origin, destination = locations
    delivery_date = timezone.localdate() + timedelta(days=day_offset)
    form = ShipmentOrderCreateForm(
        data={
            "transport": transport.pk,
            "cargo_name": "Оборудование",
            "cargo_type": "Паллеты",
            "cargo_weight_kg": "1000.00",
            "desired_delivery_date": delivery_date.isoformat(),
            "origin_location": origin.pk,
            "destination_location": destination.pk,
        }
    )

    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_create_form_uses_only_active_transports_and_locations(eco_standard):
    active_transport = Transport.objects.create(
        plate_number="А100АА777",
        model="Активный",
        category=Transport.Category.N3,
        capacity_kg=10000,
        fuel_consumption_l_per_100km=Decimal("20.00"),
        eco_standard=eco_standard,
        year=2021,
    )
    inactive_transport = Transport.objects.create(
        plate_number="А200АА777",
        model="Неактивный",
        category=Transport.Category.N3,
        capacity_kg=10000,
        fuel_consumption_l_per_100km=Decimal("20.00"),
        eco_standard=eco_standard,
        is_active=False,
        year=2020,
    )
    active_location = Location.objects.create(
        name="Активная точка",
        latitude=Decimal("55.7558"),
        longitude=Decimal("37.6173"),
    )
    inactive_location = Location.objects.create(
        name="Неактивная точка",
        latitude=Decimal("55.4312"),
        longitude=Decimal("37.5447"),
        is_active=False,
    )

    form = ShipmentOrderCreateForm()

    assert active_transport in form.fields["transport"].queryset
    assert inactive_transport not in form.fields["transport"].queryset
    assert active_location in form.fields["origin_location"].queryset
    assert inactive_location not in form.fields["origin_location"].queryset
