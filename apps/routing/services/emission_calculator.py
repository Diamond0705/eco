from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings as django_settings

from apps.routing.models import RouteOption


class EmissionCalculator:
    MODEL_V1 = "v1"
    MODEL_V2 = "v2"
    MODEL_V21 = "v2.1"
    SUPPORTED_MODELS = {MODEL_V1, MODEL_V2, MODEL_V21}
    TOLL_WARNING = (
        "Маршрут содержит платные участки, но стоимость проезда не рассчитана провайдером "
        "и не включена в итоговую стоимость перевозки."
    )
    NO_TRAFFIC_WARNING = "Провайдер не предоставляет данные о пробках, traffic_factor=1.00."
    ROAD_CLASS_FACTORS = {
        "motorway": Decimal("0.98"),
        "trunk": Decimal("1.00"),
        "primary": Decimal("1.00"),
        "secondary": Decimal("1.03"),
        "tertiary": Decimal("1.05"),
        "residential": Decimal("1.10"),
        "service": Decimal("1.12"),
        "unclassified": Decimal("1.08"),
    }
    SURFACE_FACTORS = {
        "asphalt": Decimal("1.00"),
        "concrete": Decimal("1.00"),
        "paved": Decimal("1.00"),
        "sett": Decimal("1.05"),
        "cobblestone": Decimal("1.05"),
        "gravel": Decimal("1.12"),
        "ground": Decimal("1.18"),
        "dirt": Decimal("1.18"),
        "earth": Decimal("1.18"),
    }

    def __init__(self, model_version=None):
        self.model_version = (model_version or django_settings.CALCULATION_MODEL).lower()
        if self.model_version not in self.SUPPORTED_MODELS:
            raise ValueError(
                "Неподдерживаемая версия расчетной модели. Поддерживаются: v1, v2, v2.1."
            )

    def calculate(self, order, candidate, settings):
        if self.model_version == self.MODEL_V1:
            return self._calculate_v1(order, candidate, settings)
        return self._calculate_v2(order, candidate, settings)

    def _calculate_v1(self, order, candidate, settings):
        transport = order.transport
        eco_standard = transport.eco_standard
        load_ratio = self._load_ratio(order, transport)
        load_factor = self._load_factor(load_ratio, settings)
        fuel_liters = (
            candidate.distance_km
            * transport.fuel_consumption_l_per_100km
            / Decimal("100")
            * load_factor
            * candidate.fuel_multiplier
        )
        co2_kg = fuel_liters * settings.diesel_co2_kg_per_liter
        engine_work_kwh = (
            candidate.distance_km
            * settings.engine_work_kwh_per_km
            * load_factor
            * candidate.fuel_multiplier
        )
        nox_g = engine_work_kwh * eco_standard.nox_limit_g_per_kwh
        pm_g = engine_work_kwh * eco_standard.pm_limit_mg_per_kwh / Decimal("1000")
        cost_rub = (
            fuel_liters * settings.fuel_price_rub_per_liter
            + candidate.distance_km * settings.service_tariff_rub_per_km
        )
        eco_rating = self._eco_rating(co2_kg, nox_g, pm_g, settings)

        return {
            "fuel_liters": self._round(fuel_liters, "0.01"),
            "cost_rub": self._round(cost_rub, "0.01"),
            "co2_kg": self._round(co2_kg, "0.01"),
            "nox_g": self._round(nox_g, "0.01"),
            "pm_g": self._round(pm_g, "0.001"),
            "eco_rating": self._round(eco_rating, "0.01"),
            "fuel_multiplier": self._round(candidate.fuel_multiplier, "0.01"),
            "calculation_model_version": self.MODEL_V1,
            "calculation_details_json": {
                "calculation_model_version": self.MODEL_V1,
                "load_ratio": self._json_decimal(load_ratio),
                "load_factor": self._json_decimal(load_factor),
                "final_fuel_multiplier": self._json_decimal(candidate.fuel_multiplier),
                "warnings": [],
                "formula_notes": [
                    "Модель v1: топливо считается по расстоянию, загрузке и множителю провайдера.",
                    "Стоимость включает топливо и сервисный тариф за километр.",
                ],
            },
        }

    def _calculate_v2(self, order, candidate, settings):
        transport = order.transport
        eco_standard = transport.eco_standard
        route_facts = candidate.route_facts.to_json()
        road_details = route_facts.get("road_details", {})
        warnings = list(route_facts.get("warnings", []))

        load_ratio = self._load_ratio(order, transport)
        load_factor = self._load_factor(load_ratio, settings)
        average_speed_kmh = self._average_speed_kmh(
            candidate.distance_km,
            candidate.duration_minutes,
        )
        speed_factor = self._speed_factor(average_speed_kmh)
        road_class_factor = self._weighted_factor(
            road_details.get("road_class_summary", {}),
            self.ROAD_CLASS_FACTORS,
        )
        surface_factor = self._weighted_factor(
            road_details.get("surface_summary", {}),
            self.SURFACE_FACTORS,
        )
        traffic_factor = self._traffic_factor(route_facts, candidate.duration_minutes)

        if candidate.provider == RouteOption.Provider.MOCK:
            route_fact_multiplier = Decimal("1.00")
            final_fuel_multiplier = candidate.fuel_multiplier
        else:
            route_fact_multiplier = self._clamp(
                speed_factor * road_class_factor * surface_factor * traffic_factor,
                Decimal("0.85"),
                Decimal("1.40"),
            )
            final_fuel_multiplier = route_fact_multiplier

        fuel_liters = (
            candidate.distance_km
            * transport.fuel_consumption_l_per_100km
            / Decimal("100")
            * load_factor
            * final_fuel_multiplier
        )
        co2_kg = fuel_liters * settings.diesel_co2_kg_per_liter
        engine_work_kwh = (
            candidate.distance_km
            * settings.engine_work_kwh_per_km
            * load_factor
            * final_fuel_multiplier
        )
        nox_g = engine_work_kwh * eco_standard.nox_limit_g_per_kwh
        pm_g = engine_work_kwh * eco_standard.pm_limit_mg_per_kwh / Decimal("1000")

        fuel_cost = fuel_liters * settings.fuel_price_rub_per_liter
        distance_service_cost = candidate.distance_km * settings.service_tariff_rub_per_km
        duration_hours = Decimal(candidate.duration_minutes) / Decimal("60")
        time_cost = duration_hours * settings.driver_time_tariff_rub_per_hour
        toll_cost = self._decimal_from_json(route_facts.get("toll_cost_rub", "0.00"))
        if toll_cost <= 0:
            toll_cost = Decimal("0.00")
        if route_facts.get("has_tolls") and toll_cost == 0:
            warnings.append(self.TOLL_WARNING)
        cost_rub = fuel_cost + distance_service_cost + time_cost + toll_cost

        if self.model_version == self.MODEL_V21 and not route_facts.get("supports_traffic"):
            warnings.append(self.NO_TRAFFIC_WARNING)

        intensity_details = {}
        if self.model_version == self.MODEL_V21:
            emissions_rating, intensity_details = self._eco_rating_v21(
                order,
                candidate.distance_km,
                co2_kg,
                nox_g,
                pm_g,
                settings,
            )
        else:
            emissions_rating = self._eco_rating(co2_kg, nox_g, pm_g, settings)
        route_risk_penalty = self._route_risk_penalty(
            road_details.get("surface_summary", {}),
            average_speed_kmh,
            route_facts,
        )
        eco_rating = self._clamp(
            emissions_rating - route_risk_penalty,
            Decimal("0.00"),
            Decimal("100.00"),
        )

        return {
            "fuel_liters": self._round(fuel_liters, "0.01"),
            "cost_rub": self._round(cost_rub, "0.01"),
            "co2_kg": self._round(co2_kg, "0.01"),
            "nox_g": self._round(nox_g, "0.01"),
            "pm_g": self._round(pm_g, "0.001"),
            "eco_rating": self._round(eco_rating, "0.01"),
            "fuel_multiplier": self._round(final_fuel_multiplier, "0.01"),
            "calculation_model_version": self.model_version,
            "calculation_details_json": {
                "calculation_model_version": self.model_version,
                "load_ratio": self._json_decimal(load_ratio),
                "load_factor": self._json_decimal(load_factor),
                "average_speed_kmh": self._json_decimal(average_speed_kmh),
                "speed_factor": self._json_decimal(speed_factor),
                "road_class_factor": self._json_decimal(road_class_factor),
                "surface_factor": self._json_decimal(surface_factor),
                "traffic_factor": self._json_decimal(traffic_factor),
                "route_fact_multiplier": self._json_decimal(route_fact_multiplier),
                "final_fuel_multiplier": self._json_decimal(final_fuel_multiplier),
                "fuel_cost_rub": self._json_decimal(self._round(fuel_cost, "0.01")),
                "distance_service_cost_rub": self._json_decimal(
                    self._round(distance_service_cost, "0.01")
                ),
                "time_cost_rub": self._json_decimal(self._round(time_cost, "0.01")),
                "toll_cost_rub": self._json_decimal(self._round(toll_cost, "0.01")),
                "route_risk_penalty": self._json_decimal(self._round(route_risk_penalty, "0.01")),
                **intensity_details,
                "warnings": self._deduplicate_warnings(warnings),
                "formula_notes": [
                    f"Модель {self.model_version} использует сохраненные route_facts_json "
                    "без raw-ответов провайдера.",
                    "CO2 рассчитывается по объему израсходованного дизельного топлива.",
                    "NOx и PM рассчитываются упрощенно через работу двигателя и "
                    "экологический стандарт транспорта.",
                    "Эко-рейтинг является приближенной учебной оценкой для сравнения "
                    "вариантов внутри одной заявки и не является сертифицированной "
                    "методикой EMEP/EEA/COPERT.",
                ],
            },
        }

    def _load_ratio(self, order, transport):
        return min(order.cargo_weight_kg / Decimal(transport.capacity_kg), Decimal("1"))

    def _load_factor(self, load_ratio, settings):
        return Decimal("1") + load_ratio * (
            settings.full_load_fuel_increase_percent / Decimal("100")
        )

    def _average_speed_kmh(self, distance_km, duration_minutes):
        if duration_minutes <= 0:
            return Decimal("0.00")
        return distance_km / (Decimal(duration_minutes) / Decimal("60"))

    def _speed_factor(self, average_speed_kmh):
        if average_speed_kmh < Decimal("25"):
            return Decimal("1.25")
        if average_speed_kmh < Decimal("40"):
            return Decimal("1.15")
        if average_speed_kmh < Decimal("60"):
            return Decimal("1.05")
        if average_speed_kmh <= Decimal("90"):
            return Decimal("1.00")
        return Decimal("1.08")

    def _traffic_factor(self, route_facts, duration_minutes):
        traffic_delay = self._decimal_from_json(route_facts.get("traffic_delay_minutes", 0))
        if traffic_delay <= 0 or duration_minutes <= 0:
            return Decimal("1.00")
        delay_share = min(traffic_delay / Decimal(duration_minutes), Decimal("1"))
        return Decimal("1") + delay_share * Decimal("0.20")

    def _weighted_factor(self, summary, factor_map):
        if not isinstance(summary, dict) or not summary:
            return Decimal("1.00")

        weighted_factor = Decimal("0.00")
        total_share = Decimal("0.00")
        for key, item in summary.items():
            if not isinstance(item, dict):
                continue
            share_percent = self._decimal_from_json(item.get("share_percent", 0))
            if share_percent <= 0:
                continue
            factor = factor_map.get(str(key).lower(), Decimal("1.00"))
            weighted_factor += factor * share_percent
            total_share += share_percent

        if total_share <= 0:
            return Decimal("1.00")
        missing_share = max(Decimal("0.00"), Decimal("100.00") - total_share)
        return (weighted_factor + missing_share) / Decimal("100.00")

    def _route_risk_penalty(self, surface_summary, average_speed_kmh, route_facts):
        penalty = Decimal("0.00")
        bad_surface_share = self._bad_surface_share(surface_summary)
        penalty += min(bad_surface_share / Decimal("100") * Decimal("6"), Decimal("6"))
        if average_speed_kmh < Decimal("25"):
            penalty += Decimal("2")
        if route_facts.get("has_restriction_warnings") or route_facts.get("restriction_warnings"):
            penalty += Decimal("2")
        return min(penalty, Decimal("10"))

    def _bad_surface_share(self, surface_summary):
        bad_keys = {"gravel", "ground", "dirt", "earth"}
        share = Decimal("0.00")
        if not isinstance(surface_summary, dict):
            return share
        for key, item in surface_summary.items():
            if str(key).lower() in bad_keys and isinstance(item, dict):
                share += self._decimal_from_json(item.get("share_percent", 0))
        return min(share, Decimal("100.00"))

    def _eco_rating(self, co2_kg, nox_g, pm_g, settings):
        weighted_impact = (
            settings.co2_weight * min(co2_kg / settings.co2_critical_kg, Decimal("1"))
            + settings.nox_weight * min(nox_g / settings.nox_critical_g, Decimal("1"))
            + settings.pm_weight * min(pm_g / settings.pm_critical_g, Decimal("1"))
        )
        return max(Decimal("0"), Decimal("100") * (Decimal("1") - weighted_impact))

    def _eco_rating_v21(self, order, distance_km, co2_kg, nox_g, pm_g, settings):
        if distance_km <= 0:
            co2_kg_per_km = Decimal("0.00")
            nox_g_per_km = Decimal("0.00")
            pm_g_per_km = Decimal("0.00")
        else:
            co2_kg_per_km = co2_kg / distance_km
            nox_g_per_km = nox_g / distance_km
            pm_g_per_km = pm_g / distance_km

        weighted_impact = (
            settings.co2_weight * min(co2_kg_per_km / Decimal("1.20"), Decimal("1"))
            + settings.nox_weight * min(nox_g_per_km / Decimal("6.00"), Decimal("1"))
            + settings.pm_weight * min(pm_g_per_km / Decimal("0.20"), Decimal("1"))
        )
        emissions_score = self._clamp(
            Decimal("100") * (Decimal("1") - weighted_impact),
            Decimal("0.00"),
            Decimal("100.00"),
        )
        details = {
            "co2_kg_per_km": self._json_decimal(co2_kg_per_km, "0.001"),
            "nox_g_per_km": self._json_decimal(nox_g_per_km, "0.001"),
            "pm_g_per_km": self._json_decimal(pm_g_per_km, "0.0001"),
            "emissions_score": self._json_decimal(emissions_score),
            "eco_rating_method": "v2.1_intensity_plus_route_risk",
        }
        cargo_weight_tons = order.cargo_weight_kg / Decimal("1000")
        ton_km = cargo_weight_tons * distance_km
        if ton_km > 0:
            details.update(
                {
                    "co2_kg_per_ton_km": self._json_decimal(co2_kg / ton_km, "0.0001"),
                    "nox_g_per_ton_km": self._json_decimal(nox_g / ton_km, "0.0001"),
                    "pm_g_per_ton_km": self._json_decimal(pm_g / ton_km, "0.00001"),
                }
            )
        return emissions_score, details

    def _deduplicate_warnings(self, warnings):
        unique_warnings = []
        seen = set()
        for warning in warnings:
            if not warning or warning in seen:
                continue
            seen.add(warning)
            unique_warnings.append(warning)
        return unique_warnings

    def _round(self, value, quantizer):
        return value.quantize(Decimal(quantizer), rounding=ROUND_HALF_UP)

    def _clamp(self, value, minimum, maximum):
        return min(max(value, minimum), maximum)

    def _decimal_from_json(self, value):
        try:
            return Decimal(str(value))
        except Exception:
            return Decimal("0.00")

    def _json_decimal(self, value, quantizer="0.01"):
        return str(self._round(value, quantizer))
