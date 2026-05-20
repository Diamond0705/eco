from decimal import ROUND_HALF_UP, Decimal
from math import atan2, cos, radians, sin, sqrt

from apps.routing.models import RouteOption

from .graphhopper_client import GraphHopperClient
from .providers import (
    RouteCalculationOptions,
    RouteCandidate,
    RouteFacts,
    RouteProviderCapabilities,
    RoutingProviderError,
    RoutingProviderResponseError,
)


class GraphHopperRouteProvider:
    provider = RouteOption.Provider.GRAPHHOPPER
    fuel_multiplier = Decimal("1.00")
    TOLL_WARNING = (
        "Маршрут содержит платные участки, но стоимость проезда не рассчитана провайдером "
        "и не включена в итоговую стоимость перевозки."
    )
    UNKNOWN_SPEED_WARNING = "Для части маршрута ограничение скорости неизвестно."
    UNKNOWN_SPEED_WARNING_SHARE = Decimal("25.00")

    def __init__(
        self,
        client: GraphHopperClient,
        options: RouteCalculationOptions | None = None,
    ):
        self.client = client
        self.options = options or RouteCalculationOptions()

    @property
    def capabilities(self):
        path_details = self._path_details()
        return RouteProviderCapabilities(
            provider=self.provider,
            supports_real_geometry=True,
            supports_alternatives=True,
            supports_traffic=False,
            supports_truck_routing=False,
            supports_tolls="toll" in path_details,
            supports_toll_costs=False,
            supports_road_incidents=False,
            supports_low_emission_zones=False,
            supports_road_details=bool(path_details),
            is_demo_provider=False,
        )

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
            path_details=self._path_details(),
        )
        paths = self._deduplicate_paths(self._extract_valid_paths(response))
        if not paths:
            raise RoutingProviderResponseError("GraphHopper did not return valid route paths.")

        if self._should_try_strategy_requests(paths):
            paths = self._add_strategy_paths(request_points, paths)

        paths = paths[: self.options.max_candidates]
        return [self._candidate_from_path(index, path) for index, path in enumerate(paths)]

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
                    path_details=self._path_details(),
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

    def _path_details(self):
        if not self.options.enable_path_details:
            return ()
        return tuple(detail for detail in self.options.path_details if detail)

    def _candidate_from_path(self, index, path):
        geometry = self._geometry(path)
        return RouteCandidate(
            name=self._candidate_name(index),
            provider=self.provider,
            distance_km=self._distance_km(path["distance"]),
            duration_minutes=self._duration_minutes(path["time"]),
            fuel_multiplier=self.fuel_multiplier,
            geometry_json=geometry,
            route_facts=self._route_facts(path, geometry),
        )

    def _route_facts(self, path, geometry):
        requested_details = list(self._path_details())
        if not requested_details:
            return RouteFacts.neutral(self.provider)

        details = path.get("details")
        warnings = []
        road_details = {
            "requested_details": requested_details,
            "available_details": [],
        }
        if not isinstance(details, dict):
            warnings.append("GraphHopper не вернул дорожные детали для этого маршрута.")
            return RouteFacts(
                provider=self.provider,
                road_details=road_details,
                warnings=warnings,
            )

        available_details = [
            detail for detail in requested_details if isinstance(details.get(detail), list)
        ]
        road_details["available_details"] = available_details
        for detail in requested_details:
            ranges = details.get(detail)
            if not isinstance(ranges, list):
                continue
            summary, detail_warnings = self._summarize_detail_ranges(geometry, ranges)
            road_details[f"{detail}_summary"] = summary
            warnings.extend(
                f"{detail}: {warning}"
                for warning in detail_warnings
            )

        has_tolls = self._has_tolls(road_details.get("toll_summary", {}))
        if has_tolls:
            warnings.append(self.TOLL_WARNING)
        if self._has_meaningful_unknown_speed(road_details.get("max_speed_summary", {})):
            warnings.append(self.UNKNOWN_SPEED_WARNING)

        return RouteFacts(
            provider=self.provider,
            has_tolls=has_tolls,
            toll_cost_rub=Decimal("0.00"),
            road_details=road_details,
            warnings=self._deduplicate_warnings(warnings),
        )

    def _summarize_detail_ranges(self, geometry, ranges):
        distances = {}
        counts = {}
        warnings = []
        total_distance = self._geometry_distance_km(geometry)
        used_distance = Decimal("0.00")

        for item in ranges:
            if not isinstance(item, list | tuple) or len(item) < 3:
                warnings.append("пропущен некорректный диапазон detail")
                continue
            start_index, end_index, value = item[:3]
            key = self._detail_key(value)
            counts[key] = counts.get(key, 0) + 1
            distance = self._range_distance_km(geometry, start_index, end_index)
            if distance <= 0:
                continue
            distances[key] = distances.get(key, Decimal("0.00")) + distance
            used_distance += distance

        if distances:
            denominator = total_distance if total_distance > 0 else used_distance
            return self._distance_summary(distances, denominator), warnings

        if counts:
            warnings.append("дистанции диапазонов недоступны, используется счетчик")
            return self._count_summary(counts), warnings

        return {}, warnings

    def _range_distance_km(self, geometry, start_index, end_index):
        if not isinstance(start_index, int) or not isinstance(end_index, int):
            return Decimal("0.00")
        start_index = max(start_index, 0)
        end_index = min(end_index, len(geometry) - 1)
        if end_index <= start_index:
            return Decimal("0.00")
        distance = Decimal("0.00")
        for index in range(start_index, end_index):
            distance += self._haversine_km(geometry[index], geometry[index + 1])
        return distance

    def _geometry_distance_km(self, geometry):
        distance = Decimal("0.00")
        for start, end in zip(geometry, geometry[1:], strict=False):
            distance += self._haversine_km(start, end)
        return distance

    def _haversine_km(self, start, end):
        earth_radius_km = 6371.0
        start_lat, start_lon = start
        end_lat, end_lon = end
        lat_delta = radians(end_lat - start_lat)
        lon_delta = radians(end_lon - start_lon)
        a = (
            sin(lat_delta / 2) ** 2
            + cos(radians(start_lat)) * cos(radians(end_lat)) * sin(lon_delta / 2) ** 2
        )
        distance = earth_radius_km * 2 * atan2(sqrt(a), sqrt(1 - a))
        return Decimal(str(distance))

    def _distance_summary(self, distances, total_distance):
        summary = {}
        for key, distance in distances.items():
            share_percent = Decimal("0.00")
            if total_distance > 0:
                share_percent = (distance / total_distance * Decimal("100")).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP,
                )
            summary[key] = {
                "distance_km": str(
                    distance.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                ),
                "share_percent": str(share_percent),
            }
        return summary

    def _count_summary(self, counts):
        total = sum(counts.values())
        summary = {}
        for key, count in counts.items():
            share_percent = Decimal("0.00")
            if total:
                share_percent = (Decimal(count) / Decimal(total) * Decimal("100")).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP,
                )
            summary[key] = {"count": count, "share_percent": str(share_percent)}
        return summary

    def _detail_key(self, value):
        if value is None:
            return "unknown"
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)

    def _has_tolls(self, toll_summary):
        for key, item in toll_summary.items():
            if key.lower() in {"false", "no", "none", "0", "unknown"}:
                continue
            if item.get("distance_km") and Decimal(str(item["distance_km"])) > 0:
                return True
            if item.get("count", 0) > 0:
                return True
        return False

    def _has_meaningful_unknown_speed(self, max_speed_summary):
        unknown_speed = max_speed_summary.get("unknown")
        if not isinstance(unknown_speed, dict):
            return False
        share_percent = Decimal(str(unknown_speed.get("share_percent", "0")))
        return share_percent >= self.UNKNOWN_SPEED_WARNING_SHARE

    def _deduplicate_warnings(self, warnings):
        unique_warnings = []
        seen = set()
        for warning in warnings:
            if not warning or warning in seen:
                continue
            seen.add(warning)
            unique_warnings.append(warning)
        return unique_warnings

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
