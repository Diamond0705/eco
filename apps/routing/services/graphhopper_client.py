import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .providers import RoutingProviderConfigurationError, RoutingProviderResponseError


class GraphHopperClient:
    def __init__(
        self,
        api_key,
        base_url,
        profile,
        timeout_seconds,
        opener=None,
    ):
        self.api_key = (api_key or "").strip()
        self.base_url = (base_url or "").rstrip("/")
        self.profile = profile
        self.timeout_seconds = timeout_seconds
        self.opener = opener or urlopen

    def route(
        self,
        points,
        *,
        alternative_max_paths=3,
        alternative_max_weight_factor=1.6,
        alternative_max_share_factor=0.7,
        custom_model=None,
        use_alternative_route=True,
    ):
        if not self.api_key:
            raise RoutingProviderConfigurationError(
                "GraphHopper API key is required for real routing."
            )
        if not self.base_url:
            raise RoutingProviderConfigurationError("GraphHopper base URL is required.")
        if len(points) < 2:
            raise RoutingProviderConfigurationError(
                "GraphHopper route request requires at least two points."
            )

        request = self._build_request(
            points,
            alternative_max_paths=alternative_max_paths,
            alternative_max_weight_factor=alternative_max_weight_factor,
            alternative_max_share_factor=alternative_max_share_factor,
            custom_model=custom_model,
            use_alternative_route=use_alternative_route,
        )
        try:
            response = self.opener(request, timeout=self.timeout_seconds)
            raw_body = response.read()
        except HTTPError as exc:
            raise RoutingProviderResponseError("GraphHopper returned HTTP error.") from exc
        except (TimeoutError, URLError, OSError) as exc:
            raise RoutingProviderResponseError("GraphHopper request failed.") from exc

        try:
            return json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RoutingProviderResponseError("GraphHopper returned invalid JSON.") from exc

    def _build_request(
        self,
        points,
        *,
        alternative_max_paths,
        alternative_max_weight_factor,
        alternative_max_share_factor,
        custom_model,
        use_alternative_route,
    ):
        query = urlencode({"key": self.api_key})
        payload = {
            "points": points,
            "profile": self.profile,
            "points_encoded": False,
            "calc_points": True,
            "instructions": False,
        }
        if use_alternative_route:
            payload.update(
                {
                    "algorithm": "alternative_route",
                    "alternative_route.max_paths": alternative_max_paths,
                    "alternative_route.max_weight_factor": alternative_max_weight_factor,
                    "alternative_route.max_share_factor": alternative_max_share_factor,
                }
            )
        if custom_model:
            payload["ch.disable"] = True
            payload["custom_model"] = custom_model
        return Request(
            f"{self.base_url}/route?{query}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
