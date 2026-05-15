from django.db import transaction

from apps.fleet.models import EcoCalculationSettings
from apps.orders.models import ShipmentOrder
from apps.routing.models import RouteOption

from .emission_calculator import EmissionCalculator
from .mock_provider import MockRouteProvider


class RouteCalculationService:
    def __init__(self, provider=None, calculator=None):
        self.provider = provider or MockRouteProvider()
        self.calculator = calculator or EmissionCalculator()

    @transaction.atomic
    def calculate_for_order(self, order):
        order = (
            ShipmentOrder.objects.select_for_update()
            .select_related("transport__eco_standard")
            .prefetch_related("points__location")
            .get(pk=order.pk)
        )
        if order.status not in {ShipmentOrder.Status.NEW, ShipmentOrder.Status.CALCULATED}:
            raise ValueError("Маршруты можно рассчитать только для новой или рассчитанной заявки.")

        settings = EcoCalculationSettings.get_current()
        candidates = self.provider.get_candidates(order)
        order.route_options.filter(is_selected=False).delete()

        route_options = []
        for candidate in candidates:
            calculated_values = self.calculator.calculate(order, candidate, settings)
            route_options.append(
                RouteOption.objects.create(
                    order=order,
                    name=candidate.name,
                    provider=candidate.provider,
                    distance_km=candidate.distance_km,
                    duration_minutes=candidate.duration_minutes,
                    fuel_multiplier=candidate.fuel_multiplier,
                    geometry_json=candidate.geometry_json,
                    calculation_settings=settings,
                    **calculated_values,
                )
            )

        if order.status != ShipmentOrder.Status.CALCULATED:
            order.status = ShipmentOrder.Status.CALCULATED
            order.save(update_fields=["status", "updated_at"])

        return route_options
