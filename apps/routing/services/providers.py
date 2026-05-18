from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class RouteCandidate:
    name: str
    provider: str
    distance_km: Decimal
    duration_minutes: int
    fuel_multiplier: Decimal
    geometry_json: list[list[float]]


@dataclass(frozen=True)
class RouteCalculationOptions:
    mode: str = "standard"
    requested_candidates: int = 3
    target_candidates: int = 3
    max_candidates: int = 3
    alternative_max_paths: int = 3
    alternative_max_weight_factor: float = 1.6
    alternative_max_share_factor: float = 0.7
    enable_strategy_requests: bool = False
    max_strategy_requests: int = 0


class RoutingProviderError(Exception):
    safe_message = "Не удалось получить маршруты от провайдера маршрутизации."


class RoutingProviderConfigurationError(RoutingProviderError):
    safe_message = "Провайдер маршрутизации настроен некорректно."


class RoutingProviderResponseError(RoutingProviderError):
    safe_message = "Не удалось получить маршруты от провайдера маршрутизации."
