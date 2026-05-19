from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class RouteProviderCapabilities:
    provider: str
    supports_real_geometry: bool
    supports_alternatives: bool
    supports_traffic: bool
    supports_truck_routing: bool
    supports_tolls: bool
    supports_toll_costs: bool
    supports_road_incidents: bool
    supports_low_emission_zones: bool
    supports_road_details: bool
    is_demo_provider: bool


@dataclass(frozen=True)
class RouteFacts:
    schema_version: int = 1
    provider: str = ""
    supports_traffic: bool = False
    traffic_delay_minutes: int = 0
    has_tolls: bool = False
    toll_cost_rub: Decimal = Decimal("0.00")
    has_restriction_warnings: bool = False
    restriction_warnings: list[str] = field(default_factory=list)
    road_details: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    @classmethod
    def neutral(cls, provider=""):
        return cls(provider=provider)

    def to_json(self):
        return {
            "schema_version": self.schema_version,
            "provider": self.provider,
            "supports_traffic": self.supports_traffic,
            "traffic_delay_minutes": self.traffic_delay_minutes,
            "has_tolls": self.has_tolls,
            "toll_cost_rub": str(self.toll_cost_rub.quantize(Decimal("0.01"))),
            "has_restriction_warnings": self.has_restriction_warnings,
            "restriction_warnings": list(self.restriction_warnings),
            "road_details": dict(self.road_details),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class RouteCandidate:
    name: str
    provider: str
    distance_km: Decimal
    duration_minutes: int
    fuel_multiplier: Decimal
    geometry_json: list[list[float]]
    route_facts: RouteFacts | None = None

    def __post_init__(self):
        if self.route_facts is None:
            object.__setattr__(self, "route_facts", RouteFacts.neutral(self.provider))


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
    enable_path_details: bool = False
    path_details: tuple[str, ...] = ()


class RoutingProviderError(Exception):
    safe_message = "Не удалось получить маршруты от провайдера маршрутизации."


class RoutingProviderConfigurationError(RoutingProviderError):
    safe_message = "Провайдер маршрутизации настроен некорректно."


class RoutingProviderResponseError(RoutingProviderError):
    safe_message = "Не удалось получить маршруты от провайдера маршрутизации."
