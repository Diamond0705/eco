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
