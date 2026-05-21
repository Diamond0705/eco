from decimal import (
    ROUND_HALF_UP,
    Decimal,
    InvalidOperation,
)

MISSING_VALUE = "—"
TOLL_WITHOUT_COST_NOTICE = (
    "На маршруте есть платные участки. Их стоимость не включена в итоговую стоимость перевозки."
)


def route_snapshot_details(route):
    details = route.calculation_details_json
    if isinstance(details, dict):
        return details
    return {}


def route_snapshot_facts(route):
    facts = route.route_facts_json
    if isinstance(facts, dict):
        return facts
    return {}


def calculation_model_version(route):
    details = route_snapshot_details(route)
    return (
        details.get("calculation_model_version")
        or route.calculation_model_version
        or MISSING_VALUE
    )


def co2_kg_per_km(route):
    return _decimal_from_details(route, "co2_kg_per_km")


def co2_kg_per_ton_km(route):
    return _decimal_from_details(route, "co2_kg_per_ton_km")


def final_fuel_multiplier(route):
    return _decimal_from_details(route, "final_fuel_multiplier")


def average_speed_kmh(route):
    return _decimal_from_details(route, "average_speed_kmh")


def route_warnings(route):
    facts = route_snapshot_facts(route)
    details = route_snapshot_details(route)
    warnings = []
    for source in (facts.get("warnings"), details.get("warnings")):
        if isinstance(source, list):
            warnings.extend(str(warning) for warning in source if warning)
    if has_unpriced_tolls(route):
        warnings.append(TOLL_WITHOUT_COST_NOTICE)
    return _deduplicate(warnings)


def has_tolls(route):
    facts = route_snapshot_facts(route)
    if facts.get("has_tolls") is True:
        return True
    return any(_is_toll_warning(warning) for warning in route_warnings(route))


def has_unpriced_tolls(route):
    facts = route_snapshot_facts(route)
    if facts.get("has_tolls") is not True:
        return any(_is_toll_warning(warning) for warning in _raw_warnings(route))
    toll_cost = decimal_from_snapshot(facts.get("toll_cost_rub", "0.00"))
    return toll_cost is None or toll_cost == Decimal("0.00")


def display_decimal(value, quantizer="0.01"):
    if value is None:
        return MISSING_VALUE
    return str(value.quantize(Decimal(quantizer), rounding=ROUND_HALF_UP))


def average_decimal(values, quantizer="0.01"):
    values = [value for value in values if value is not None]
    if not values:
        return None
    return (sum(values, Decimal("0.00")) / Decimal(len(values))).quantize(
        Decimal(quantizer),
        rounding=ROUND_HALF_UP,
    )


def decimal_from_snapshot(value):
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _decimal_from_details(route, key):
    return decimal_from_snapshot(route_snapshot_details(route).get(key))


def _raw_warnings(route):
    facts = route_snapshot_facts(route)
    details = route_snapshot_details(route)
    warnings = []
    for source in (facts.get("warnings"), details.get("warnings")):
        if isinstance(source, list):
            warnings.extend(str(warning) for warning in source if warning)
    return warnings


def _is_toll_warning(warning):
    normalized = str(warning).lower()
    return (
        "платн" in normalized
        or "стоимость проезда" in normalized
        or "toll" in normalized
    )


def _deduplicate(items):
    result = []
    seen = set()
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result
