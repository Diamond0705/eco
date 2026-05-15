from django.db import transaction
from django.utils import timezone

from apps.orders.models import ShipmentOrder
from apps.routing.models import RouteOption

from .models import Trip, TripStatusEvent


class TripLifecycleService:
    @transaction.atomic
    def approve_route(self, order, route_option, user):
        order = (
            ShipmentOrder.objects.select_for_update()
            .select_related("manager")
            .get(pk=order.pk)
        )
        route_option = RouteOption.objects.select_for_update().get(pk=route_option.pk)

        if order.manager_id != user.pk:
            raise ValueError("Можно утверждать маршруты только для своих заявок.")
        if route_option.order_id != order.pk:
            raise ValueError("Маршрут не относится к выбранной заявке.")
        if hasattr(order, "trip"):
            raise ValueError("Для этой заявки уже создан рейс.")
        if order.status != ShipmentOrder.Status.CALCULATED:
            raise ValueError("Маршрут можно утвердить только для рассчитанной заявки.")

        order.route_options.select_for_update().exclude(pk=route_option.pk).update(
            is_selected=False
        )
        if not route_option.is_selected:
            route_option.is_selected = True
            route_option.save(update_fields=["is_selected", "updated_at"])

        order.status = ShipmentOrder.Status.PLANNED
        order.save(update_fields=["status", "updated_at"])

        trip = Trip.objects.create(
            order=order,
            route_option=route_option,
            status=Trip.Status.PLANNED,
        )
        self._create_event(
            trip=trip,
            old_status="",
            new_status=Trip.Status.PLANNED,
            user=user,
            comment="Маршрут утвержден, рейс запланирован.",
        )
        return trip

    @transaction.atomic
    def start_trip(self, trip, user, actual_start_at=None, comment=""):
        trip = Trip.objects.select_for_update().select_related("order__manager").get(pk=trip.pk)
        if trip.order.manager_id != user.pk:
            raise ValueError("Можно изменять только свои рейсы.")
        if trip.status != Trip.Status.PLANNED:
            raise ValueError("Начать можно только запланированный рейс.")

        actual_start_at = actual_start_at or timezone.now()
        old_status = trip.status
        trip.status = Trip.Status.IN_PROGRESS
        trip.actual_start_at = actual_start_at
        trip.save(update_fields=["status", "actual_start_at", "updated_at"])
        self._create_event(
            trip=trip,
            old_status=old_status,
            new_status=Trip.Status.IN_PROGRESS,
            user=user,
            comment=comment or "Рейс начат.",
            event_at=actual_start_at,
        )
        return trip

    @transaction.atomic
    def deliver_trip(self, trip, user, actual_finish_at=None, comment=""):
        trip = Trip.objects.select_for_update().select_related("order__manager").get(pk=trip.pk)
        if trip.order.manager_id != user.pk:
            raise ValueError("Можно изменять только свои рейсы.")
        if trip.status != Trip.Status.IN_PROGRESS:
            raise ValueError("Завершить можно только рейс в пути.")

        actual_finish_at = actual_finish_at or timezone.now()
        if trip.actual_start_at and actual_finish_at < trip.actual_start_at:
            raise ValueError("Фактическое завершение не может быть раньше фактического начала.")

        old_status = trip.status
        trip.status = Trip.Status.DELIVERED
        trip.actual_finish_at = actual_finish_at
        trip.save(update_fields=["status", "actual_finish_at", "updated_at"])

        order = trip.order
        order.status = ShipmentOrder.Status.COMPLETED
        order.save(update_fields=["status", "updated_at"])

        self._create_event(
            trip=trip,
            old_status=old_status,
            new_status=Trip.Status.DELIVERED,
            user=user,
            comment=comment or "Рейс завершен.",
            event_at=actual_finish_at,
        )
        return trip

    def _create_event(self, trip, old_status, new_status, user, comment="", event_at=None):
        return TripStatusEvent.objects.create(
            trip=trip,
            old_status=old_status,
            new_status=new_status,
            changed_by=user,
            event_at=event_at,
            comment=comment,
        )
