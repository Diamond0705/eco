# CHANGELOG

## Phase 20 - JWT API Auth

- Added SimpleJWT access, refresh and verify endpoints under `/api/v1/auth/`.
- Added `/api/v1/auth/me/` with safe current-user fields for API clients.
- Added Bearer-token authentication while keeping Django session authentication for the HTML web UI.
- Kept the business API read-only and left CORS, OAuth, Swagger/OpenAPI UI, token blacklist,
  refresh rotation, write API, migrations, providers and calculation formulas unchanged.

## Phase 19 - Read-Only REST API

- Added a session-authenticated read-only Django REST Framework API under `/api/v1/`.
- Added locations, transports, orders, order detail, trips and analytics summary endpoints.
- Kept API responses limited to safe snapshot data; raw provider payloads, storage paths and full
  calculation details are not exposed.
- Kept existing HTML views, business workflows, routing providers, calculation formulas, JWT,
  CORS, Swagger/OpenAPI UI, Celery/Redis/PostGIS and migrations unchanged.

## Phase 18 - Security, Waitress And Nginx Deploy Prep

- Added deployment-oriented security settings for secure cookies, HSTS, proxy SSL headers,
  trusted CSRF origins and console logging.
- Added Waitress as the approved WSGI server for Windows-friendly deployment; Gunicorn is not used.
- Added Docker, Nginx and deployment compose files for a production-style reverse-proxy setup.
- Added `/healthz/` and deployment documentation with collectstatic and manual PostgreSQL backup
  notes.
- Kept local `runserver`, business logic, routing providers, calculation formulas, REST/JWT,
  Celery/Redis/PostGIS and migrations unchanged.

## Phase 17 - Private Document Archive

- Added private archive records for generated PDF/XLSX documents with authorized Django downloads.
- Added local-by-default document storage with optional MinIO/S3-compatible backend through `django-storages[s3]`.
- Added archive save actions for emissions PDF/XLSX, trip list XLSX, trip waybill PDF and admin analytics XLSX.
- Kept direct PDF/XLSX downloads, routing providers, calculation formulas, REST/JWT/Celery/Redis/PostGIS scope and static files unchanged.

## Phase 16 - Excel Export And Technical Roadmap

- Added synchronous `.xlsx` exports for manager emissions reports, admin company analytics and manager trip lists.
- Added `openpyxl` as the only approved Excel export dependency; no pandas or numpy reporting stack was introduced.
- Added `docs/16_technical_roadmap.md` for production-grade future phases.
- Kept routing providers, calculation formulas, old `RouteOption` snapshots, REST/JWT/MinIO/Celery/PostGIS scope and migrations unchanged.

## Phase 15.1 - UI Polish And Safe Demo Cleanup

- Added `clear_operational_data --yes` for local/demo cleanup of obsolete orders, points, route options, trips and trip status events.
- Kept users, transport, locations, eco standards, calculation settings, groups, permissions, migrations and tables unchanged.
- Polished small admin-panel labels, helper text and action wording without changing providers, formulas or dependencies.

## Phase 15 - In-App Admin Panel CRUD

- Added in-application administrator pages for users, transport, locations, eco standards and calculation settings.
- Cleaned up the admin dashboard KPI grid and added admin-panel navigation.
- Kept Django Admin available for extended editing.
- Kept providers, calculation formulas, dependencies, migrations and old `RouteOption` snapshots unchanged.

## Phase 14 - Reports Explainability

- Added compact route calculation summaries to waybill PDFs from saved `RouteOption` snapshots.
- Added emissions intensity, average eco-rating and toll-route indicators to reports and analytics.
- Added vehicle Euro class to waybill and emissions report outputs.
- Kept formulas, providers, dependencies, migrations and old route snapshots unchanged.

## Phase 13 - Calculation Model v2.1

- Added route distance scope with `MAX_ROUTE_DISTANCE_KM=2000` for new calculations.
- Added Calculation Model v2.1 with intensity-based educational eco-rating and saved intensity details.
- Added deduplicated calculation warnings for traffic gaps, toll cost gaps and unknown speed data.
- Updated route comparison to show calculation details and deterministic best eco badge handling.
- Kept GraphHopper, MockRouteProvider, existing snapshots, reports, PDFs, analytics and migrations stable.

## Reference Data Expansion

- Added `seed_reference_expansion` command for additional route-testing reference data.
- Added legacy Euro I-II standards, expanded Russian locations and five demo transports.
- Kept routing logic, calculation formulas, models and migrations unchanged.

## Phase 12 - Calculation Model v2

- Added Calculation Model v2 for new route calculations from saved normalized route facts.
- Added route calculation metadata snapshots with model version and calculation details JSON.
- Added driver time tariff to eco calculation settings and v2 route cost.
- Kept old RouteOption snapshots, providers, reports, PDFs and analytics behavior stable.

## Phase 11 - GraphHopper Route Facts

- Added optional GraphHopper path details requests for normalized route facts.
- Enriched `RouteOption.route_facts_json` with road class, environment, surface, speed and toll summaries.
- Kept emission, cost, eco-rating, reports, PDFs and analytics behavior unchanged.

## Phase 8.1 - GraphHopper Alternatives

- Added standard and extended route calculation modes for GraphHopper alternatives.
- Tuned GraphHopper alternative route settings and capped real candidates at five.
- Added deduplication and best-effort strategy requests without fabricating route options.
- Added route comparison diagnostics for requested and found alternatives.

## Phase 8 - Real Routing Provider

- Added optional GraphHopper routing behind the existing provider boundary.
- Kept mock routing as the default and fallback provider.
- Updated route comparison to support a variable number of real alternatives.

## MVP Final Polish

- Added case-insensitive duplicate email validation to profile editing.
- Clarified implemented MVP documentation, mock routing status and Phase 8 provider boundary.
- Added a concise post-MVP security and deployment checklist.

## Phase 7 - Analytics And MVP Polish

- Added manager analytics at `/analytics/`.
- Enhanced admin dashboard with company-wide counters and delivered-trip totals.
- Replaced placeholder dashboard cards with real counters.
- Improved waybill and emissions PDF visual layout.
- Updated MVP documentation and final scope guards.

## Phase 6 - PDF Reports

- Added PDF waybill download for trips.
- Added manager emissions report page and PDF.
- Added ReportLab Cyrillic font helper.

## Phase 5 - Trips

- Added route approval.
- Added Trip and TripStatusEvent lifecycle from planned to delivered.
- Added trip list, trip detail and status actions.

## Phase 4 - Mock Routing

- Added RouteOption snapshots.
- Added deterministic mock route calculation.
- Added route comparison page with Leaflet map and route table.

## Phase 3 - Orders

- Added ShipmentOrder and OrderPoint.
- Added order list, create, detail, edit, cancel and status filter.

## Phase 2 - Fleet And Locations

- Added eco standards, transports, eco calculation settings and locations.
- Added demo seed command and admin registrations.

## Phase 1 - Accounts

- Added custom user flows, profile, login/logout, manager registration and role dashboards.

## Phase 0 - Skeleton

- Added Django monolith skeleton, custom user model, PostgreSQL settings, docs, tests and ruff setup.
