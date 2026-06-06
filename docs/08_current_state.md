# Current MVP State

EcoLogist MVP is complete through Phase 8.1. Phase 9 is a documentation/specification phase and does not change application behavior.
Фаза 12 включает расчетную модель v2 для новых маршрутов: она использует сохраненные
`route_facts_json`, сохраняет версию модели и детали расчета, но не пересчитывает старые
`RouteOption` и не меняет поведение отчетов, PDF, аналитики или рейсов.
Фаза 10 добавляет внутренний контракт capabilities/facts и JSON-снимок фактов маршрута; она не
меняет пользовательский сценарий, формулы расчета, отчеты, PDF или аналитику.
Фаза 11 обогащает `route_facts_json` нормализованными дорожными деталями GraphHopper; формулы,
отчеты, PDF, аналитика и пользовательский сценарий остаются прежними.

This file is the current implementation snapshot. Docs `00` through `07` are historical and
planning notes for earlier phases, so they may describe target behavior or old phase boundaries.
Фаза 9 является исследовательской и спецификационной: она описывает стратегию провайдеров и
расчетную модель v2, но сама по себе не меняет поведение приложения.

## Phase 15.1

- Added `clear_operational_data --yes` for local/demo cleanup of obsolete operational data:
  shipment orders, order points, route options, trips and trip status events.
- The cleanup command does not delete users, transport, locations, eco standards,
  calculation settings, groups or permissions.
- Small admin-panel UI labels and helper texts were polished without changing routing
  providers, calculation formulas, dependencies or migrations.

## Phase 16

- Added synchronous Excel `.xlsx` downloads for manager emissions reports, admin company
  analytics and manager trip lists.
- Excel exports are generated in memory with `openpyxl` and are not saved to media, database or
  object storage.
- Exports use saved `RouteOption` snapshot fields and `calculation_details_json`; old snapshots
  without intensity metrics show `—` instead of being recalculated.
- Added `docs/16_technical_roadmap.md` for later production-grade work: MinIO, production deploy,
  REST API, Celery/Redis, PostGIS/geozones and security hardening.
- Routing providers, calculation formulas, REST/JWT/MinIO/Celery/PostGIS implementation scope and
  migrations remain unchanged.

## Phase 17

- Added a private document archive for generated PDF and Excel files.
- Archive files are saved through Django storage: local media by default, optional private
  MinIO/S3-compatible storage when `USE_S3_STORAGE=True`.
- Managers see only their own archived documents; admins and superusers see the company archive.
- Archived documents are downloaded only through authorized Django views, not through public
  MinIO/S3 URLs.
- Existing direct PDF/XLSX downloads remain available and do not automatically create archive
  records.
- User avatars, company logo upload, REST API, JWT, Celery/Redis, PostGIS, production deployment,
  routing providers and calculation formulas remain out of this phase.

## Phase 18

- Added production-style security settings controlled by environment variables while keeping
  local Windows `runserver` over HTTP working by default.
- Added Waitress as the WSGI app server for deployment and Nginx as a reverse proxy for static
  files and dynamic Django requests.
- Added Docker deployment files separate from the local development `docker-compose.yml`.
- Added `/healthz/` for simple container health checks.
- Private archived documents remain protected by Django views; Nginx serves collected static
  files only and does not expose archive storage.
- Gunicorn, REST API, JWT, Celery/Redis, PostGIS, provider changes, formula changes and scheduled
  backups remain out of this phase.

## Phase 19

- Added a read-only Django REST Framework API under `/api/v1/`.
- API access uses Django session authentication and existing manager/admin data scoping.
- Managers can read only their own orders, trips and analytics; admins and superusers can read
  company-level data.
- API route summaries expose saved `RouteOption` snapshot fields and safe intensity metrics only.
- Full `calculation_details_json`, raw provider data, geometry, storage paths and detailed personal
  manager data are not exposed.
- JWT, CORS, Swagger/OpenAPI UI, write API, migrations, provider changes and formula changes remain
  out of this phase.

## Phase 20

- Added JWT authentication for external REST API clients with SimpleJWT.
- Added token obtain, refresh and verify endpoints under `/api/v1/auth/`.
- Added `/api/v1/auth/me/` with safe current-user fields: `id`, `username`, `full_name`, `role`.
- Existing web UI authentication remains Django session based.
- Business API endpoints remain read-only and keep the same manager/admin scoping rules.
- Token blacklist, refresh rotation, token logout, CORS, OAuth, Swagger/OpenAPI UI, write API,
  migrations, provider changes and formula changes remain out of this phase.

## Phase 21

- Added OpenAPI schema generation at `/api/schema/`.
- Added Swagger UI at `/api/docs/` and ReDoc at `/api/redoc/` for the existing read-only API.
- Swagger can use JWT Bearer authorization obtained from `/api/v1/auth/token/`.
- The schema can be imported into Postman.
- Business API endpoints remain read-only; CORS, write API, migrations, provider changes,
  formula changes, PDF/XLSX/archive changes and HTML view changes remain out of this phase.

## Implemented

- Russian-only Django monolith with custom `accounts.User`.
- Manager registration, login/logout, profile and role-based access.
- Fleet, eco standards, calculation settings singleton and demo locations.
- Shipment orders with ordered points, edit/cancel rules and status filtering.
- Deterministic mock route calculation with Leaflet route comparison.
- Route approval that creates one Trip per order.
- Trip lifecycle: planned, in progress, delivered.
- PDF waybill and emissions PDF through ReportLab.
- Excel exports for emissions reports, company analytics and trip lists.
- Private archive for generated PDF/XLSX documents.
- Production-style deployment preparation with Waitress, Nginx and env-driven security settings.
- Read-only session-authenticated API for integrations.
- JWT Bearer authentication for external read-only API clients.
- OpenAPI schema, Swagger UI and ReDoc for API inspection and Postman import.
- Manager emissions report and analytics.
- Admin company dashboard with real counters.

## Routing And Snapshots

- Default routing uses deterministic `MockRouteProvider` data.
- Phase 8 adds optional `GraphHopperRouteProvider` real routing.
- `MockRouteProvider` returns three demo routes.
- `GraphHopperRouteProvider` returns the available real alternatives from the provider and does
  not duplicate routes to force three options.
- Standard GraphHopper calculation requests up to 3 real alternatives.
- Extended GraphHopper calculation requests up to 5 real alternatives and may run limited
  best-effort strategy requests.
- `GraphHopperRouteProvider` returns the same internal `RouteCandidate` format.
- Views, templates, trips, reports and analytics must not consume raw external routing responses.
- Analytics and reports use saved `RouteOption` snapshots, including distance, duration, fuel,
  cost, emissions, eco-rating, geometry and calculation settings reference.
- The best eco route is determined after calculation from saved route facts, not assigned before
  the environmental calculation.
- Existing `RouteOption` values must not be recalculated automatically when settings change.
- GraphHopper route facts may include normalized road details from path details, but raw provider
  responses are still not stored or exposed.
- New calculations use Calculation Model v2 by default and store `calculation_model_version` and
  `calculation_details_json` as part of the route snapshot.
- Phase 13 updates new calculations to Calculation Model v2.1. Routes above
  `MAX_ROUTE_DISTANCE_KM=2000` are filtered or rejected before replacing old options.
- v2.1 stores emissions intensity fields in `calculation_details_json` and uses them for an
  educational comparative eco-rating while keeping absolute CO2/NOx/PM snapshot values unchanged.
- Route comparison shows compact Russian calculation details, deduplicated warnings and one
  deterministic best eco route badge.
- Phase 14 extends waybill PDFs, emissions reports and analytics with compact explainability
  metrics from saved `RouteOption` snapshots and `calculation_details_json`.
- Reports now show average CO2 intensity, average eco-rating, toll-route counts and vehicle Euro
  class where relevant, without recalculating old route options.
- Phase 15 expands the in-application administrator panel with CRUD pages for common reference
  data and calculation settings while keeping Django Admin available for extended editing.
- Existing saved `RouteOption` rows remain historical snapshots and are not recalculated
  automatically.

## Demo Flow

1. Run `python manage.py seed_demo`.
2. Log in as `manager_demo` / `Manager12345!`.
3. Create an order, calculate routes and compare route options.
4. Approve a route, start the trip and deliver it.
5. Download the waybill PDF.
6. Review reports and analytics.

## Known Limits

- Mock routes remain the default for local demos.
- GraphHopper is optional and requires an API key.
- Traffic, roadworks, truck restrictions and GPS tracking are out of scope.
- Excel export is implemented synchronously for practical reports; generated files can now be
  saved manually to the private document archive, while background exports remain out of scope.
- Production-style deployment preparation is available, but full managed VPS/cloud operations,
  TLS certificate automation and scheduled backups are not implemented.
- The REST API is read-only, supports session and JWT authentication, and includes OpenAPI/Swagger
  documentation. CORS and write endpoints are not implemented.
- Environmental calculations are intentionally simplified for educational use.

## Before Public Deployment

- Set `DEBUG=False`.
- Read `SECRET_KEY` from the environment only.
- Configure `ALLOWED_HOSTS`.
- Review HTTPS, secure cookies and HSTS settings.
- Keep `.env` out of git.
- Keep the GraphHopper API key out of git when Phase 8 is implemented.
- Protect media and PDF access behind authorization.
- Configure PostgreSQL backups.
- Consider the personal data policy for names, email, phone, route history and trip history.
- Review tile, CDN and provider privacy before using real routes.
