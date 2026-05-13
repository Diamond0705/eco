# Mock-маршруты

MVP использует только `MockRouteProvider`.

## Правила

- Внешние API не вызываются.
- Свободный ввод адресов и геокодинг не используются.
- Маршруты строятся по predefined-точкам из `locations.Location`.
- Leaflet рисует `geometry_json` как polyline.
- Внутренний формат `geometry_json`: `[[lat, lon], ...]`.

## RouteCandidate

Все providers должны возвращать единый внутренний формат `RouteCandidate`.

`fuel_multiplier` задается provider-ом автоматически:

- `fast = 1.08`
- `short = 1.00`
- `eco = 0.92`

`GraphHopperRouteProvider` можно добавить только после готового MVP, без изменения views, templates, reports и analytics.
