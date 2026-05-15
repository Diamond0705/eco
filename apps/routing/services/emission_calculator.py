from decimal import ROUND_HALF_UP, Decimal


class EmissionCalculator:
    def calculate(self, order, candidate, settings):
        transport = order.transport
        eco_standard = transport.eco_standard
        load_ratio = min(order.cargo_weight_kg / Decimal(transport.capacity_kg), Decimal("1"))
        load_factor = Decimal("1") + load_ratio * (
            settings.full_load_fuel_increase_percent / Decimal("100")
        )
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
        }

    def _eco_rating(self, co2_kg, nox_g, pm_g, settings):
        weighted_impact = (
            settings.co2_weight * min(co2_kg / settings.co2_critical_kg, Decimal("1"))
            + settings.nox_weight * min(nox_g / settings.nox_critical_g, Decimal("1"))
            + settings.pm_weight * min(pm_g / settings.pm_critical_g, Decimal("1"))
        )
        return max(Decimal("0"), Decimal("100") * (Decimal("1") - weighted_impact))

    def _round(self, value, quantizer):
        return value.quantize(Decimal(quantizer), rounding=ROUND_HALF_UP)
