from decimal import ROUND_HALF_UP, Decimal

from apps.routing.models import RouteOption

from .graphhopper_client import GraphHopperClient
from .providers import (
    RouteCalculationOptions,
    RouteCandidate,
    RoutingProviderError,
    RoutingProviderResponseError,
)


class GraphHopperRouteProvider:
    provider = RouteOption.Provider.GRAPHHOPPER
    fuel_multiplier = Decimal("1.00")

    def __init__(
        self,
        client: GraphHopperClient,
        options: RouteCalculationOptions | None = None,
    ):
        self.client = client
        self.options = options or RouteCalculationOptions()

    def get_candidates(self, order):
        points = list(order.points.select_related("location").order_by("sequence"))
        if len(points) < 2:
            raise RoutingProviderResponseError(
                "Для расчета маршрута нужны минимум две точки."
            )

        request_points = [
            [float(point.location.longitude), float(point.location.latitude)] for point in points
        ]
        response = self.client.route(
            request_points,
            alternative_max_paths=self.options.alternative_max_paths,
            alternative_max_weight_factor=self.options.alternative_max_weight_factor,
            alternative_max_share_factor=self.options.alternative_max_share_factor,
        )
        paths = self._deduplicate_paths(self._extract_valid_paths(response))
        if not paths:
            raise RoutingProviderResponseError("GraphHopper did not return valid route paths.")

        if self._should_try_strategy_requests(paths):
            paths = self._add_strategy_paths(request_points, paths)

        paths = paths[: self.options.max_candidates]
        return [
            RouteCandidate(
                name=self._candidate_name(index),
                provider=self.provider,
                distance_km=self._distance_km(path["distance"]),
                duration_minutes=self._duration_minutes(path["time"]),
                fuel_multiplier=self.fuel_multiplier,
                geometry_json=self._geometry(path),
            )
            for index, path in enumerate(paths)
        ]

    def _should_try_strategy_requests(self, paths):
        return (
            self.options.enable_strategy_requests
            and self.options.max_strategy_requests > 0
            and len(paths) < self.options.target_candidates
            and len(paths) < self.options.max_candidates
        )

    def _add_strategy_paths(self, request_points, paths):
        combined_paths = list(paths)
        for custom_model in self._strategy_models()[: self.options.max_strategy_requests]:
            if len(combined_paths) >= self.options.target_candidates:
                break
            try:
                response = self.client.route(
                    request_points,
                    custom_model=custom_model,
                    use_alternative_route=False,
                )
                strategy_paths = self._extract_valid_paths(response)
            except RoutingProviderError:
                continue
            combined_paths = self._deduplicate_paths(
                [*combined_paths, *strategy_paths]
            )
            combined_paths = combined_paths[: self.options.max_candidates]
        return combined_paths

    def _strategy_models(self):
        return [
            {
                "distance_influence": 120,
            },
            {
                "distance_influence": 90,
                "priority": [
                    {
                        "if": "road_class == MOTORWAY",
                        "multiply_by": "0.75",
                    }
                ],
            },
        ]

    def _extract_valid_paths(self, response):
        paths = response.get("paths")
        if not isinstance(paths, list):
            raise RoutingProviderResponseError("GraphHopper response does not contain paths.")

        valid_paths = []
        for path in paths:
            if not isinstance(path, dict):
                continue
            points = path.get("points")
            if not isinstance(points, dict):
                continue
            coordinates = points.get("coordinates")
            distance = path.get("distance")
            duration = path.get("time")
            if not isinstance(coordinates, list) or len(coordinates) < 2:
                continue
            if not isinstance(distance, int | float) or not isinstance(duration, int | float):
                continue
            if distance <= 0 or duration < 0:
                continue
            valid_paths.append(path)
        return valid_paths

    def _deduplicate_paths(self, paths):
        unique_paths = []
        exact_signatures = set()
        for path in paths:
            exact_signature = self._exact_geometry_signature(path)
            if exact_signature in exact_signatures:
                continue
            if any(self._looks_like_same_path(path, existing) for existing in unique_paths):
                continue
            exact_signatures.add(exact_signature)
            unique_paths.append(path)
            if len(unique_paths) >= self.options.max_candidates:
                break
        return unique_paths

    def _exact_geometry_signature(self, path):
        return tuple(
            (round(float(coordinate[0]), 6), round(float(coordinate[1]), 6))
            for coordinate in path["points"]["coordinates"]
            if isinstance(coordinate, list | tuple) and len(coordinate) >= 2
        )

    def _looks_like_same_path(self, path, existing_path):
        if not self._metrics_nearly_equal(path, existing_path):
            return False
        return self._sampled_geometry_signature(path) == self._sampled_geometry_signature(
            existing_path
        )

    def _metrics_nearly_equal(self, path, existing_path):
        distance_delta = abs(float(path["distance"]) - float(existing_path["distance"]))
        time_delta = abs(float(path["time"]) - float(existing_path["time"]))
        distance_limit = max(100, float(existing_path["distance"]) * 0.01)
        time_limit = max(60000, float(existing_path["time"]) * 0.01)
        return distance_delta <= distance_limit and time_delta <= time_limit

    def _sampled_geometry_signature(self, path):
        coordinates = [
            coordinate
            for coordinate in path["points"]["coordinates"]
            if isinstance(coordinate, list | tuple) and len(coordinate) >= 2
        ]
        if len(coordinates) <= 5:
            sample = coordinates
        else:
            sample_indexes = {
                0,
                len(coordinates) // 4,
                len(coordinates) // 2,
                (len(coordinates) * 3) // 4,
                len(coordinates) - 1,
            }
            sample = [coordinates[index] for index in sorted(sample_indexes)]
        return tuple((round(float(lon), 4), round(float(lat), 4)) for lon, lat, *_ in sample)

    def _candidate_name(self, index):
        if index == 0:
            return "Маршрут GraphHopper"
        return f"Альтернативный маршрут {index}"

    def _geometry(self, path):
        coordinates = path["points"]["coordinates"]
        geometry = []
        for coordinate in coordinates:
            if not isinstance(coordinate, list | tuple) or len(coordinate) < 2:
                continue
            lon, lat = coordinate[:2]
            geometry.append([round(float(lat), 6), round(float(lon), 6)])
        if len(geometry) < 2:
            raise RoutingProviderResponseError("GraphHopper route geometry is invalid.")
        return geometry

    def _distance_km(self, distance_meters):
        return (Decimal(str(distance_meters)) / Decimal("1000")).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    def _duration_minutes(self, duration_milliseconds):
        minutes = Decimal(str(duration_milliseconds)) / Decimal("60000")
        return max(1, int(minutes.to_integral_value(rounding=ROUND_HALF_UP)))
