# Phase 19 REST API

Phase 19 adds a small read-only integration API on top of the existing Django monolith. It does
not replace the Russian server-rendered UI and does not introduce a write API.

## Purpose

- Provide stable machine-readable data for internal integrations and future clients.
- Reuse existing Django sessions and role-based access rules.
- Expose saved operational snapshots without recalculating routes, emissions or costs.

## Authentication

- API access uses Django session authentication.
- Phase 20 also adds JWT authentication for external clients.
- Anonymous requests are rejected by Django REST Framework permissions.
- Existing web UI pages continue to use Django sessions.
- CORS is not configured in this phase.
- Swagger/OpenAPI UI is not added in this phase.

## Endpoints

All endpoints are mounted under `/api/v1/` and are read-only. `POST`, `PUT`, `PATCH` and
`DELETE` return `405 Method Not Allowed`.

- `GET /api/v1/locations/` - active locations.
- `GET /api/v1/transports/` - active transport with Euro standard summary.
- `GET /api/v1/orders/` - manager's own orders or all orders for admins/superusers.
- `GET /api/v1/orders/<id>/` - order detail with points and safe route option summaries.
- `GET /api/v1/trips/` - trips with optional `status`, `date_from`, `date_to` filters.
- `GET /api/v1/analytics/summary/` - delivered-trip summary from saved route snapshots.

## Access Rules

- Managers can read only their own orders, trips and analytics.
- Admins and superusers can read company-level data.
- A manager receives `404` when requesting another manager's order detail through the API.
- Manager identity is intentionally minimal: `id`, `username` and `full_name` only.

## Data Exposure

The API does not expose password hashes, phone numbers, email addresses, MinIO/S3 paths, secrets,
raw GraphHopper responses, `route_facts_json`, geometry or full `calculation_details_json`.

Route summaries use saved `RouteOption` snapshot fields only:

```json
{
  "id": 1,
  "name": "Маршрут GraphHopper",
  "is_selected": true,
  "distance_km": "100.00",
  "duration_minutes": 120,
  "fuel_liters": "32.50",
  "cost_rub": "10000.00",
  "co2_kg": "80.00",
  "nox_g": "24.00",
  "pm_g": "0.400",
  "eco_rating": "75.00",
  "calculation_model_version": "v2.1",
  "co2_kg_per_km": "0.800",
  "co2_kg_per_ton_km": "0.1600"
}
```

`Trip.planned_finish` is returned as `null` because the current model has no planned finish field;
no migration is introduced for this compatibility layer.

## Limitations

- No write API.
- No CORS policy for browser-based external clients.
- No OpenAPI/Swagger UI dependency.
- No pagination, throttling or public integration contract beyond the Phase 19 read-only endpoints.
- JWT is limited to Phase 20 token endpoints and Bearer access for the same read-only API.
