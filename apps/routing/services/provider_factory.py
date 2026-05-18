from django.conf import settings

from .graphhopper_client import GraphHopperClient
from .graphhopper_provider import GraphHopperRouteProvider
from .mock_provider import MockRouteProvider
from .providers import RouteCalculationOptions, RoutingProviderConfigurationError

STANDARD_MODE = "standard"
EXTENDED_MODE = "extended"
MAX_GRAPHHOPPER_CANDIDATES = 5


def get_route_provider(options=None):
    provider_name = settings.ROUTE_PROVIDER.lower()
    if provider_name == "mock":
        return MockRouteProvider()
    if provider_name == "graphhopper":
        options = options or build_route_calculation_options()
        return GraphHopperRouteProvider(
            GraphHopperClient(
                api_key=settings.GRAPHHOPPER_API_KEY,
                base_url=settings.GRAPHHOPPER_BASE_URL,
                profile=settings.GRAPHHOPPER_PROFILE,
                timeout_seconds=settings.GRAPHHOPPER_TIMEOUT_SECONDS,
            ),
            options=options,
        )
    raise RoutingProviderConfigurationError(
        f"Unknown route provider configured: {settings.ROUTE_PROVIDER}"
    )


def build_route_calculation_options(mode=STANDARD_MODE, *, allow_strategy_requests=None):
    mode = _normalize_mode(mode)
    mode_limit = 5 if mode == EXTENDED_MODE else 3
    max_candidates = min(
        _clamp_int(settings.GRAPHHOPPER_MAX_CANDIDATES, 1, MAX_GRAPHHOPPER_CANDIDATES),
        mode_limit,
    )
    requested_candidates = max_candidates
    alternative_max_paths = min(
        _clamp_int(
            settings.GRAPHHOPPER_ALTERNATIVE_MAX_PATHS,
            1,
            MAX_GRAPHHOPPER_CANDIDATES,
        ),
        max_candidates,
    )
    target_candidates = min(
        _clamp_int(settings.GRAPHHOPPER_TARGET_CANDIDATES, 1, MAX_GRAPHHOPPER_CANDIDATES),
        max_candidates,
    )
    max_strategy_requests = 0
    if mode == EXTENDED_MODE:
        max_strategy_requests = _clamp_int(settings.GRAPHHOPPER_MAX_STRATEGY_REQUESTS, 0, 2)
    if allow_strategy_requests is None:
        allow_strategy_requests = settings.GRAPHHOPPER_ENABLE_STRATEGY_REQUESTS
    return RouteCalculationOptions(
        mode=mode,
        requested_candidates=requested_candidates,
        target_candidates=target_candidates,
        max_candidates=max_candidates,
        alternative_max_paths=alternative_max_paths,
        alternative_max_weight_factor=settings.GRAPHHOPPER_ALTERNATIVE_MAX_WEIGHT_FACTOR,
        alternative_max_share_factor=settings.GRAPHHOPPER_ALTERNATIVE_MAX_SHARE_FACTOR,
        enable_strategy_requests=(
            mode == EXTENDED_MODE and bool(allow_strategy_requests) and max_strategy_requests > 0
        ),
        max_strategy_requests=max_strategy_requests,
    )


def _normalize_mode(mode):
    mode = (mode or STANDARD_MODE).lower()
    if mode == EXTENDED_MODE:
        return EXTENDED_MODE
    return STANDARD_MODE


def _clamp_int(value, minimum, maximum):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return minimum
    return min(max(value, minimum), maximum)
