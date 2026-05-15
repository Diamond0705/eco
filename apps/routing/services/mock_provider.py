from decimal import Decimal
from math import atan2, cos, radians, sin, sqrt

from apps.routing.models import RouteOption

from .providers import RouteCandidate


class MockRouteProvider:
    provider = RouteOption.Provider.MOCK

    route_profiles = (
        {
            "name": "Быстрый",
            "fuel_multiplier": Decimal("1.08"),
            "distance_factor": Decimal("1.04"),
            "speed_kmh": Decimal("70"),
            "offset": 0.010,
            "curve": (0.003, 0.006, 0.006, 0.003),
        },
        {
            "name": "Короткий",
            "fuel_multiplier": Decimal("1.00"),
            "distance_factor": Decimal("1.02"),
            "speed_kmh": Decimal("55"),
            "offset": 0.000,
            "curve": (0.001, -0.001, 0.001, -0.001),
        },
        {
            "name": "Экологичный",
            "fuel_multiplier": Decimal("0.92"),
            "distance_factor": Decimal("1.03"),
            "speed_kmh": Decimal("60"),
            "offset": -0.010,
            "curve": (-0.003, -0.006, -0.006, -0.003),
        },
    )
    interpolation_steps = (0.20, 0.40, 0.60, 0.80)
    predefined_corridors = {
        frozenset(("Москва", "Подольск")): {
            "Быстрый": [(55.6398, 37.6225), (55.5346, 37.5968)],
            "Короткий": [(55.6495, 37.6028), (55.5402, 37.5704)],
            "Экологичный": [(55.6678, 37.5488), (55.5518, 37.5202)],
        },
        frozenset(("Москва", "Химки")): {
            "Быстрый": [(55.8103, 37.5525), (55.8581, 37.4807)],
            "Короткий": [(55.8004, 37.5706), (55.8507, 37.5014)],
            "Экологичный": [(55.7929, 37.5278), (55.8427, 37.4564)],
        },
        frozenset(("Москва", "Мытищи")): {
            "Быстрый": [(55.8175, 37.6614), (55.8694, 37.7032)],
            "Короткий": [(55.8101, 37.6818), (55.8607, 37.7178)],
            "Экологичный": [(55.8287, 37.6385), (55.8791, 37.6834)],
        },
        frozenset(("Москва", "Балашиха")): {
            "Быстрый": [(55.7755, 37.7356), (55.7897, 37.8534)],
            "Короткий": [(55.7642, 37.7481), (55.7784, 37.8558)],
            "Экологичный": [(55.7411, 37.7172), (55.7564, 37.8397)],
        },
        frozenset(("Одинцово", "Подольск")): {
            "Быстрый": [(55.6105, 37.3324), (55.5148, 37.4264)],
            "Короткий": [(55.5922, 37.3597), (55.4992, 37.4526)],
            "Экологичный": [(55.6351, 37.2918), (55.5369, 37.4017)],
        },
        frozenset(("Люберцы", "Мытищи")): {
            "Быстрый": [(55.7621, 37.8841), (55.8542, 37.8154)],
            "Короткий": [(55.7528, 37.8587), (55.8422, 37.7873)],
            "Экологичный": [(55.7259, 37.8343), (55.8299, 37.7572)],
        },
        frozenset(("Домодедово", "Люберцы")): {
            "Быстрый": [(55.5042, 37.8161), (55.5958, 37.8652)],
            "Короткий": [(55.4935, 37.7923), (55.5908, 37.8434)],
            "Экологичный": [(55.5254, 37.7568), (55.6118, 37.8128)],
        },
    }

    def get_candidates(self, order):
        points = list(order.points.select_related("location").order_by("sequence"))
        if len(points) < 2:
            raise ValueError("Для расчета маршрута нужны минимум две точки.")

        coordinates = [
            (float(point.location.latitude), float(point.location.longitude)) for point in points
        ]
        base_distance_km = sum(
            self._haversine_km(start, end)
            for start, end in zip(coordinates, coordinates[1:], strict=False)
        )

        return [
            self._build_candidate(profile, points, coordinates, base_distance_km)
            for profile in self.route_profiles
        ]

    def _build_candidate(self, profile, points, coordinates, base_distance_km):
        geometry = self._build_geometry(points, coordinates, profile)
        geometry_distance_km = sum(
            self._haversine_km(start, end)
            for start, end in zip(geometry, geometry[1:], strict=False)
        )
        distance_km = (
            Decimal(str(max(base_distance_km, geometry_distance_km))) * profile["distance_factor"]
        ).quantize(
            Decimal("0.01")
        )
        duration_minutes = max(
            1,
            int(((distance_km / profile["speed_kmh"]) * Decimal("60")).to_integral_value()),
        )

        return RouteCandidate(
            name=profile["name"],
            provider=self.provider,
            distance_km=distance_km,
            duration_minutes=duration_minutes,
            fuel_multiplier=profile["fuel_multiplier"],
            geometry_json=geometry,
        )

    def _build_geometry(self, points, coordinates, profile):
        geometry = [list(coordinates[0])]
        for index, (start, end) in enumerate(zip(coordinates, coordinates[1:], strict=False)):
            start_name = points[index].location.name
            end_name = points[index + 1].location.name
            waypoints = self._segment_waypoints(start_name, end_name, start, end, profile)
            for segment_start, segment_end in zip(waypoints, waypoints[1:], strict=False):
                geometry.extend(
                    self._interpolate_corridor(
                        segment_start,
                        segment_end,
                        profile,
                        include_end=True,
                    )
                )
        return [[round(lat, 6), round(lon, 6)] for lat, lon in geometry]

    def _segment_waypoints(self, start_name, end_name, start, end, profile):
        corridor = self.predefined_corridors.get(frozenset((start_name, end_name)), {})
        via_points = corridor.get(profile["name"], [])
        if start_name > end_name:
            via_points = list(reversed(via_points))
        return [start, *via_points, end]

    def _interpolate_corridor(self, start, end, profile, include_end=False):
        points = []
        for step, bend in zip(self.interpolation_steps, profile["curve"], strict=True):
            points.append(self._offset_point(start, end, step, profile["offset"] + bend))
        if include_end:
            points.append(list(end))
        return points

    def _offset_point(self, start, end, step, offset):
        start_lat, start_lon = start
        end_lat, end_lon = end
        delta_lat = end_lat - start_lat
        delta_lon = end_lon - start_lon
        length = sqrt(delta_lat**2 + delta_lon**2) or 1
        base_lat = start_lat + delta_lat * step
        base_lon = start_lon + delta_lon * step
        return [base_lat - (delta_lon / length) * offset, base_lon + (delta_lat / length) * offset]

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
        return earth_radius_km * 2 * atan2(sqrt(a), sqrt(1 - a))
