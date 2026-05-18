from django.conf import settings
from django.db import transaction

from apps.fleet.models import EcoCalculationSettings
from apps.orders.models import ShipmentOrder
from apps.routing.models import RouteOption

from .emission_calculator import EmissionCalculator
from .mock_provider import MockRouteProvider
from .provider_factory import (
    EXTENDED_MODE,
    build_route_calculation_options,
    get_route_provider,
)
from .providers import RoutingProviderError, RoutingProviderResponseError


class RouteCalculationService:
    def __init__(self, provider=None, calculator=None, calculation_mode="standard"):
        self.provider = provider
        self.calculator = calculator or EmissionCalculator()
        self.calculation_mode = calculation_mode
        self.last_warning = ""
        self.last_requested_count = 0
        self.last_found_count = 0
        self.last_used_provider = ""

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

        calculation_settings = EcoCalculationSettings.get_current()
        candidates = self._get_candidates(order)
        order.route_options.filter(is_selected=False).delete()

        route_options = []
        for candidate in candidates:
            calculated_values = self.calculator.calculate(order, candidate, calculation_settings)
            route_options.append(
                RouteOption.objects.create(
                    order=order,
                    name=candidate.name,
                    provider=candidate.provider,
                    distance_km=candidate.distance_km,
                    duration_minutes=candidate.duration_minutes,
                    fuel_multiplier=candidate.fuel_multiplier,
                    geometry_json=candidate.geometry_json,
                    calculation_settings=calculation_settings,
                    **calculated_values,
                )
            )

        if order.status != ShipmentOrder.Status.CALCULATED:
            order.status = ShipmentOrder.Status.CALCULATED
            order.save(update_fields=["status", "updated_at"])

        return route_options

    def _get_candidates(self, order):
        options = build_route_calculation_options(
            self.calculation_mode,
            allow_strategy_requests=self.calculation_mode == EXTENDED_MODE,
        )
        self.last_requested_count = options.requested_candidates
        try:
            provider = self.provider or get_route_provider(options)
            candidates = provider.get_candidates(order)
        except RoutingProviderError as exc:
            if not self._should_fallback_to_mock():
                raise ValueError(exc.safe_message) from exc
            self.last_warning = (
                "GraphHopper недоступен, поэтому маршруты рассчитаны "
                "демонстрационным mock-провайдером."
            )
            provider = MockRouteProvider()
            candidates = provider.get_candidates(order)

        if not candidates:
            raise ValueError(RoutingProviderResponseError.safe_message)
        self.last_found_count = len(candidates)
        self.last_used_provider = getattr(provider, "provider", "") or candidates[0].provider
        return candidates

    def _should_fallback_to_mock(self):
        return (
            self.provider is None
            and settings.ROUTE_PROVIDER.lower() == RouteOption.Provider.GRAPHHOPPER
            and settings.GRAPHHOPPER_FALLBACK_TO_MOCK
        )
