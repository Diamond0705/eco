# Phase 24 Manager API Expansion

Phase 24 expands the existing Django REST Framework API so the future React manager SPA can run
the core operational workflow through JSON endpoints. Django templates remain available, and the
backend business services, models, route providers, calculations, reports and snapshots remain the
source of truth.

This phase does not add React files, frontend dependencies, database migrations, CORS, WebSocket,
Celery or Redis.

## Scope

- Manager dashboard API.
- Manager order create, edit and cancel API.
- Route calculation API with polling-compatible status endpoint.
- Route options API with safe `geometry_json` for React Leaflet.
- Route approval API that creates a trip through `TripLifecycleService`.
- Trip detail, start and deliver API.
- Manager emissions report JSON API.
- OpenAPI schema coverage and tests for the new endpoints.

Admin SPA CRUD, document archive API and React scaffold remain later phases.

## Endpoints

Existing JWT endpoints remain unchanged:

- `POST /api/v1/auth/token/`
- `POST /api/v1/auth/token/refresh/`
- `POST /api/v1/auth/token/verify/`
- `GET /api/v1/auth/me/`

Reference and read endpoints:

- `GET /api/v1/locations/`
- `GET /api/v1/transports/`
- `GET /api/v1/orders/`
- `GET /api/v1/orders/<id>/`
- `GET /api/v1/trips/`
- `GET /api/v1/trips/<id>/`
- `GET /api/v1/analytics/summary/`
- `GET /api/v1/manager/dashboard/`
- `GET /api/v1/reports/emissions/`

Manager write/action endpoints:

- `POST /api/v1/orders/`
- `PATCH /api/v1/orders/<id>/`
- `POST /api/v1/orders/<id>/cancel/`
- `POST /api/v1/orders/<id>/calculate-routes/`
- `GET /api/v1/orders/<id>/route-calculation-status/`
- `GET /api/v1/orders/<id>/route-options/`
- `POST /api/v1/orders/<order_id>/routes/<route_option_id>/approve/`
- `POST /api/v1/trips/<id>/start/`
- `POST /api/v1/trips/<id>/deliver/`

## Access Rules

- Anonymous requests are rejected.
- Managers can create and mutate only their own operational data.
- Managers receive `404` when attempting actions on another manager's order or trip.
- Admins and superusers keep company-level read access where it already existed.
- Manager write/action endpoints return `403` for non-manager users.
- Django sessions still work for legacy templates and Django Admin.
- JWT Bearer auth works for the expanded API.

## Data Exposure

- Route option API now exposes `geometry_json` to authenticated users who can access the order.
- Internal format remains `[[lat, lon], ...]`.
- API responses still do not expose password hashes, secrets, MinIO/S3 paths, raw GraphHopper
  responses, `route_facts_json` or full `calculation_details_json`.
- Route calculation details are limited to UI-safe summary fields and deduplicated warnings.
- Saved `RouteOption` snapshots are returned as stored; old snapshots are not recalculated.

## React Contract Notes

Order create and patch use these JSON fields:

```json
{
  "transport": 1,
  "cargo_name": "Cargo",
  "cargo_type": "Type",
  "cargo_weight_kg": "5000.00",
  "delivery_date": "2026-06-08",
  "origin_location": 1,
  "destination_location": 2,
  "notes": ""
}
```

Route calculation accepts an optional `route_calculation_mode` value of `standard` or `extended`.
The calculation currently remains synchronous, but
`GET /api/v1/orders/<id>/route-calculation-status/` provides the polling-compatible surface for
the React client.

Trip start and deliver accept optional actual timestamps and comments:

```json
{
  "actual_start": "2026-06-08T10:00:00+03:00",
  "comment": "Started through API"
}
```

```json
{
  "actual_finish": "2026-06-08T12:00:00+03:00",
  "comment": "Delivered through API"
}
```

## Tests

Phase 24 adds and updates tests for:

- session-authenticated and JWT-authenticated manager API writes;
- validation errors for order payloads;
- manager scoping and cross-manager rejection;
- route calculation and route geometry exposure;
- route approval, trip start and trip delivery;
- dashboard and emissions report JSON from saved snapshots;
- OpenAPI documentation for Phase 24 paths and methods.
