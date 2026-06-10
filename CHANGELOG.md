# CHANGELOG

## Phase 37 - React Registration Error Handling Fix

- Stabilized manager registration API validation errors so field errors are returned as arrays of
  Russian strings for React.
- Improved React registration error rendering for duplicate username/email, invalid fields,
  network failures and request timeout.
- Restored registration phone auto-formatting from `89...`/`79...` to `+7 (...) ...` on blur and
  removed the post-registration login success banner.
- Added a registration request timeout to prevent an endless `Регистрируем...` state.
- Extended Playwright auth smoke coverage for the duplicate manager registration scenario.
- Kept models, migrations, registration rules, JWT login/refresh behavior and Django templates
  unchanged.

## Phase 36 - React Auth Template Parity And Registration

- Reworked unauthenticated React auth screens to match the Django login/register templates:
  white header, EcoLogist logo, template font stack, leaf background and soft white cards.
- Added public manager registration API at `/api/v1/auth/register/` using the existing
  `ManagerRegistrationForm` validation and manager role assignment.
- Added React `/register` flow with Russian labels, field-level API errors and post-success
  redirect back to `/login`.
- Extended React smoke tests and backend API tests for auth screen rendering and manager
  registration behavior.
- Kept database models, migrations, business logic, JWT login/refresh flow, Django templates and
  Django Admin unchanged.

## Phase 35 - React Manager UI Template Parity

- Reworked the manager React layout to match the Django template header: white top navigation,
  EcoLogist logo, green links and dashboard background.
- Updated manager dashboard, order creation and archive pages toward Django-template visual parity
  with metric cards, sectioned forms, archive filters, file icons and table actions.
- Added a lightweight React manager analytics route for the restored `Аналитика` navigation item
  using existing dashboard API data.
- Refined shared React UI components and CSS so manager orders, trips, reports, archive and profile
  pages share the same panel/card/form/table visual language.
- Kept backend APIs, models, migrations, calculations, route providers, Django templates, Django
  Admin, admin-specific React pages and dependencies unchanged.

## Phase 34 - Final Demo Readiness And Documentation Alignment

- Aligned README and current-state documentation with the final React SPA + Django REST API
  architecture.
- Added a final demo readiness runbook covering local development, production-like deploy,
  manager/admin/API demos, demo data cleanup and verification commands.
- Clarified that Django templates and Django sessions remain for legacy/fallback views and Django
  Admin, while React SPA is the main user-facing interface.
- Documented runtime artifact hygiene for `.env`, `.tmp`, frontend build folders and
  `protected_media/`.
- Kept business logic, models, migrations, calculations, routing providers, React runtime behavior,
  deploy logic, secrets, Celery, Redis, WebSockets and PostGIS unchanged.

## Phase 33 - CI Pipeline And Automated Quality Checks

- Added GitHub Actions CI for backend checks, migration drift checks, pytest, ruff, frontend
  dependency installation and React production build.
- Added a deploy configuration job that validates `docker-compose.deploy.yml` without building or
  pulling the full production stack.
- Documented CI environment values, local reproduction commands and why Playwright E2E remains a
  local smoke check for now.
- Kept business logic, models, migrations, calculations, routing providers, React runtime behavior,
  reports, archive services, Celery, Redis, WebSockets and secrets unchanged.

## Phase 32 - React UI Stabilization And E2E Smoke Tests

- Added Playwright smoke tests for the React manager and administrator SPA navigation, login,
  protected-route redirects and role access boundaries.
- Added frontend E2E scripts and Playwright configuration for local Vite development with the
  Django backend running separately.
- Documented the local E2E setup, demo credentials strategy and intentionally excluded heavy
  browser coverage such as real GraphHopper routing and visual regression.
- Kept business logic, models, migrations, calculations, routing providers, reports, archive
  services, Celery, Redis, WebSockets and Django templates unchanged.

## Phase 31 - React Admin SPA

- Added admin-only REST API endpoints under `/api/v1/admin/` for the company dashboard, Excel
  export/archive actions, users, transports, locations, eco standards and calculation settings.
- Added a React administrator area with a separate top-navigation layout, dashboard cards,
  reference CRUD pages, user activity controls and calculation settings version creation.
- Extended `/api/v1/auth/me/` with derived `is_admin` for React route guards while keeping Django
  Admin and legacy Django templates available.
- Updated Nginx routing so selected `/admin/...` React routes serve the SPA while `/admin/` still
  reaches Django Admin.
- Kept models, migrations, formulas, route providers, reports, archive services, Celery, Redis and
  WebSockets unchanged.

## Phase 30 - React Nginx Production Deploy

- Added a dedicated Nginx Docker build that builds the React SPA with Node and serves the compiled
  assets from Nginx.
- Updated production-like Nginx routing so `/` and React client routes use SPA fallback while
  `/api/`, `/admin/`, `/healthz/` and protected backend download/action paths proxy to Django.
- Kept Django/Waitress as the backend application server and kept Django static files served from
  the existing `static_data` volume.
- Kept MinIO internal by default in deploy compose; public MinIO debug ports should be added only
  through a local override.
- Kept business logic, models, migrations, calculations, providers, reports, archive/profile logic,
  admin SPA, Celery, Redis and WebSockets unchanged.

## Phase 29 - React Profile Avatar

- Added React `/profile` page with editable personal data and protected avatar upload/delete.
- Added `/api/v1/profile/` and `/api/v1/profile/avatar/` for current-user profile and avatar
  actions.
- Extended avatar validation to JPG, PNG and WEBP with a 5 MB limit and header checks.
- Added a local default avatar SVG and kept raw avatar storage paths out of API responses.
- Kept Django templates, login/logout behavior, models, migrations, calculations, route providers,
  reports, archive behavior, admin SPA and deploy files unchanged.

## Phase 28 - React Trips, Reports And Archive

- Added React manager pages for trips list/detail, trip start/deliver actions, emissions reports
  and private document archive.
- Added JWT-protected API endpoints for emissions PDF/XLSX downloads, report archive saves, trip
  Excel export, waybill PDF download/archive and archive list/download/delete.
- Kept all report, waybill, Excel and archive generation on existing Django services.
- Kept Django templates, backend models, migrations, route providers, calculation formulas, admin
  SPA, CORS, WebSocket, Celery and Redis unchanged.

## Phase 27 - React Route Comparison And Approval

- Added React route calculation and comparison page at `/orders/:id/routes`.
- Added React Leaflet map rendering from saved `geometry_json` route snapshots.
- Added route option cards with provider, badges, warnings, metrics and calculation details.
- Added route approval through the existing Django API while keeping trip creation on the backend.
- Kept Django templates, backend views, models, migrations, formulas, providers, reports, archive,
  admin SPA, trips/reports React pages, CORS, WebSocket, Celery and Redis unchanged.

## Phase 26 - Manager SPA Core

- Added React manager dashboard, orders list, order create and order detail pages.
- Added RTK Query manager API hooks for dashboard, orders, order detail/create/cancel, transports
  and locations.
- Added lightweight project UI components for cards, buttons, badges, tables, forms, alerts and
  loading states.
- Kept Django templates, backend business logic, models, migrations, route calculation UI, Leaflet
  route comparison, admin SPA, CORS, WebSocket, Celery and Redis unchanged.

## Phase 25 - React SPA Scaffold

- Added a Vite React SPA scaffold under `/frontend` using JavaScript, React Router, Redux Toolkit,
  RTK Query and React Redux.
- Added JWT login flow, current-user loading, in-memory access token state, `sessionStorage`
  refresh token storage, refresh-on-401 retry and logout clearing.
- Added protected and role-based routes plus a Russian EcoLogist shell with login, dashboard
  placeholder and not-found pages.
- Kept Django templates, backend views, models, migrations, business logic, CORS, WebSocket,
  Celery, Redis and full manager/admin SPA pages unchanged.

## Phase 24 - Manager API Expansion

- Added manager-facing DRF write/action endpoints for orders, route calculation, route options,
  route approval, trip detail/start/deliver, dashboard and emissions report JSON.
- Exposed authorized route `geometry_json` for the future React Leaflet map while keeping raw
  provider data and full calculation internals hidden.
- Kept Django templates, sessions, business services, models, route providers, formulas, reports,
  archive behavior, migrations, CORS, WebSocket, Celery, Redis and frontend files unchanged.
- Updated API, JWT and OpenAPI tests for the expanded manager API contract.

## Phase 23 - React SPA Foundation Plan

- Added `docs/23_react_spa_foundation.md` with the approved React SPA migration architecture.
- Recorded React, Vite, React Router, Redux Toolkit, RTK Query and React Leaflet as planned
  frontend technologies for later phases.
- Documented API gaps, JWT handling, polling-first status updates, migration phases and test
  strategy.
- Kept code, dependencies, migrations, templates, existing API behavior, providers, formulas,
  reports and deployment files unchanged.

## Phase 21 - API Docs And Swagger

- Added OpenAPI schema generation with drf-spectacular at `/api/schema/`.
- Added Swagger UI at `/api/docs/` and ReDoc at `/api/redoc/` for inspecting the existing API.
- Documented JWT Bearer authorization in Swagger and OpenAPI import into Postman.
- Kept the business API read-only and left CORS, write endpoints, providers, formulas, reports,
  archives, HTML views and migrations unchanged.

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
