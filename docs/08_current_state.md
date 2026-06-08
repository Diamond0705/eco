# Current Project State

EcoLogist is complete through Phase 37 for final demonstration readiness.

The current architecture is React SPA + Django REST API:

- React SPA is the main user-facing interface.
- Django templates still exist as legacy/fallback/internal views.
- Django Admin remains available at `/admin/`.
- Django REST Framework exposes JSON API under `/api/v1/`.
- SimpleJWT Bearer tokens are used for React/API authentication.
- React exposes template-matched login and manager registration screens.
- Public API manager registration is available at `/api/v1/auth/register/`.
- React registration shows field-level validation errors and times out stalled requests.
- Django sessions remain for Django Admin and legacy/template views.
- Nginx serves the React build and proxies backend routes to Django/Waitress.
- PostgreSQL stores application data.
- MinIO/S3-compatible storage can store protected documents and avatar media when enabled.
- GraphHopper remains the real routing integration behind the provider boundary; mock routing
  remains the default for deterministic local demos.
- Leaflet/OpenStreetMap are used client-side for map display.

The original Django-template MVP was complete through Phase 8.1. Phase 9 was a
documentation/specification phase and did not change application behavior.
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

## Phase 23

- Added `docs/23_react_spa_foundation.md` as the React SPA migration foundation plan.
- React, Vite, React Router, Redux Toolkit, RTK Query and React Leaflet are approved for later
  phases as an explicit project scope change.
- The target architecture keeps Django, DRF, PostgreSQL, existing services, routing providers,
  calculations, reports and saved snapshots as the backend source of truth.
- Phase 23 itself adds no frontend files, dependencies, migrations, write API endpoints, CORS,
  WebSocket, Celery or Redis.

## Phase 24

- Added manager-facing DRF endpoints for order create/edit/cancel, route calculation, route
  calculation status, route options, route approval, trip detail/start/deliver, manager dashboard
  and emissions report JSON.
- Route option API exposes authorized `geometry_json` for the future React Leaflet map while
  continuing to hide raw provider payloads, `route_facts_json` and full
  `calculation_details_json`.
- Existing Django templates and session-based web UI remain available.
- No React files, frontend dependencies, migrations, CORS, WebSocket, Celery, Redis, provider
  changes or calculation formula changes are added in this phase.

## Phase 25

- Added `/frontend` as a Vite React JavaScript SPA scaffold.
- Added React Router, Redux Toolkit, RTK Query and React Redux frontend structure.
- Added login, current-user loading, protected routes, role routes, logout, Russian layout shell,
  placeholder dashboard and not-found page.
- Vite proxies `/api` and `/static` to Django on `http://127.0.0.1:8000`, so CORS remains
  unconfigured.
- Existing Django templates, backend views, models, migrations, business logic, route providers,
  calculation formulas, PDF/XLSX/archive behavior, WebSocket, Celery and Redis remain unchanged.

## Phase 26

- Added the first real manager React workflow: dashboard, orders list, order create and order
  detail.
- Added RTK Query manager API hooks for dashboard, orders, order detail/create/cancel, transports
  and locations.
- Added lightweight React UI components for cards, buttons, badges, data tables, fields, alerts
  and loading states.
- Route calculation UI, Leaflet route comparison and admin React pages remain deferred.
- Existing Django templates, backend views, models, migrations, business logic, route providers,
  formulas, PDF/XLSX/archive behavior, CORS, WebSocket, Celery and Redis remain unchanged.

## Phase 27

- Added React route calculation and comparison at `/orders/:id/routes`.
- Added React Leaflet and Leaflet frontend dependencies for route maps.
- The route comparison page renders saved `geometry_json`, route metrics, backend badges,
  warnings and calculation details.
- Managers can approve a route through the existing backend API; trip creation remains in Django.
- Existing Django templates, backend views, models, migrations, calculation formulas, routing
  providers, PDF/XLSX/archive behavior, admin React pages, trips/reports React pages, CORS,
  WebSocket, Celery and Redis remain unchanged.

## Phase 28

- Added React manager pages for trips, trip detail/status actions, emissions reports and document
  archive.
- Added JWT-protected API endpoints for report PDF/XLSX downloads, report archive saves, trip
  Excel export, waybill PDF actions and archive list/download/delete.
- React file downloads use the REST API with Bearer auth, so they do not require Django session
  cookies.
- Existing Django templates, backend models, migrations, route providers, calculation formulas,
  report/archive services, CORS, WebSocket, Celery and Redis remain unchanged.

## Phase 29

- Added React `/profile` page for current-user profile viewing/editing and avatar management.
- Added current-user profile API endpoints under `/api/v1/profile/`.
- Avatar upload/download/delete is protected by API authentication and does not expose raw storage
  paths or public MinIO/S3 URLs.
- Avatar validation allows JPG, PNG and WEBP up to 5 MB with extension, content-type and file
  header checks.
- Existing Django profile pages, login/logout flow, calculations, route providers, reports,
  archive behavior, admin React pages and deployment files remain unchanged.

## Phase 30

- Updated production-like Docker/Nginx deployment so Nginx builds and serves the React SPA.
- React client routes now use Nginx SPA fallback in deploy mode.
- `/api/`, `/admin/`, `/healthz/` and selected protected legacy download/action paths still proxy
  to Django/Waitress.
- Django collected static files continue to be served from the `static_data` volume.
- MinIO remains internal by default in deploy compose; public debug ports should be added only via
  local override.
- Waitress remains the WSGI server. Gunicorn, Celery, Redis, WebSockets, admin React SPA,
  migrations and business logic changes remain out of scope.

## Phase 31

- Added React administrator pages for the company dashboard, archive, users, transport, locations,
  eco standards, calculation settings and profile.
- Added admin-only REST API endpoints under `/api/v1/admin/` for dashboard data, Excel
  download/archive actions, reference CRUD and calculation settings version creation.
- Added derived `is_admin` to `/api/v1/auth/me/` so React can allow both admin-role users and
  superusers into the admin SPA.
- Nginx now serves selected React `/admin/...` routes while keeping `/admin/` itself proxied to
  Django Admin.
- Existing Django templates, Django Admin, models, migrations, formulas, route providers, reports,
  archive services, CORS, Celery, Redis and WebSockets remain unchanged.

## Phase 32

- Added Playwright E2E smoke tests for React manager and administrator navigation, login,
  protected-route redirects and role access boundaries.
- Added frontend E2E scripts and Playwright configuration for local Vite development with Django
  running separately on `http://127.0.0.1:8000`.
- E2E tests use demo users from `seed_demo` by default and do not create or destroy business data.
- Real GraphHopper, full visual regression, production monitoring, Celery, Redis, WebSockets,
  PostGIS, model changes and migrations remain out of scope.

## Phase 33

- Added GitHub Actions CI under `.github/workflows/ci.yml`.
- Backend CI runs Django checks, migration drift detection, pytest and ruff against PostgreSQL 16
  with dummy CI-only environment values.
- Frontend CI installs `/frontend` dependencies with `npm ci` and builds the Vite React SPA.
- Deploy CI validates `docker-compose.deploy.yml` with a dummy `.env` file but does not build or
  pull the production images.
- Playwright E2E remains a local smoke check because it requires an already running Django backend,
  PostgreSQL, demo seed data and a Vite server.
- No business logic, models, migrations, calculations, routing providers, React behavior, secrets,
  Celery, Redis or WebSockets are changed.

## Phase 34

- Aligned final documentation with the React SPA + Django REST API architecture.
- Added `docs/34_final_demo_readiness.md` as the final demo runbook.
- Clarified local development, production-like deploy, manager/admin/API demos, demo data reset,
  security notes and verification commands.
- Added `protected_media/` to `.gitignore` as runtime protected storage.
- No business logic, models, migrations, calculations, routing providers, React behavior, deploy
  logic, Celery, Redis, WebSockets or PostGIS are changed.

## Phase 35

- Reworked the manager React SPA visual layer to follow the existing Django-template design.
- Manager React now uses a white top navigation, EcoLogist logo, dashboard background, broad
  translucent panels, green cards, sectioned forms, archive file icons and template-like tables.
- Added `/analytics` as a lightweight manager React page using existing dashboard API data.
- Admin-specific React pages are not redesigned in this phase.
- Backend APIs, models, migrations, calculations, routing providers, Django templates, Django Admin,
  dependencies and deploy logic remain unchanged.

## Phase 36

- React `/login` and `/register` now match the Django auth template visual language: white
  header, EcoLogist logo, leaf background, card background, green buttons and Russian-only text.
- Added `POST /api/v1/auth/register/` for public manager account creation using the existing
  `ManagerRegistrationForm` validation and role assignment.
- Successful React registration redirects to `/login` with a completion message instead of
  auto-login, matching the Django template flow.
- Models, migrations, JWT token obtain/refresh behavior, Django templates and Django Admin remain
  unchanged.

## Phase 37

- React manager registration now shows duplicate username/email warnings under the matching fields
  instead of leaving the form in a loading state.
- Registration API validation errors are normalized as arrays of Russian strings for predictable
  React rendering.
- The React registration request has a timeout and shows a general message for server/network
  failures.
- Models, migrations, registration rules, JWT login/refresh behavior and Django templates remain
  unchanged.

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
- React SPA migration plan for later phases.
- Manager workflow API used by the React SPA.
- Vite React SPA scaffold with JWT auth shell.
- Manager React dashboard and order workflow.
- React route calculation, Leaflet comparison map and route approval.
- React manager trips, emissions reports and document archive.
- React current-user profile with protected avatar upload/delete.
- Production-like Nginx deploy path serving the React SPA and proxying Django API/Admin.
- React administrator SPA for company dashboard, admin archive, user activity, reference CRUD and
  calculation settings versions.
- Playwright smoke coverage for core React manager/admin routes.
- GitHub Actions CI for backend, frontend and deploy compose validation.
- Final demo readiness documentation and runbook.
- Manager React UI parity with the Django-template visual language.
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

See `docs/34_final_demo_readiness.md` for the full final demo runbook.

Short flow:

1. Run `python manage.py seed_demo`.
2. Open the React SPA and log in as `manager_demo` / `Manager12345!`.
3. Create an order, calculate routes, compare route options on the map and approve a route.
4. Open the created trip, start and deliver it if desired.
5. Review reports, download PDF/XLSX documents and save documents to the archive.
6. Log in as `admin_demo` / `Admin12345!` and show the admin React dashboard, reference pages,
   archive and the Django Admin link.

## Known Limits

- Mock routes remain the default for local demos.
- GraphHopper is optional and requires an API key.
- Traffic, roadworks, truck restrictions and GPS tracking are out of scope.
- Excel export is implemented synchronously for practical reports; generated files can now be
  saved manually to the private document archive, while background exports remain out of scope.
- Production-style deployment preparation is available, but full managed VPS/cloud operations,
  TLS certificate automation and scheduled backups are not implemented.
- The REST API supports session and JWT authentication, includes OpenAPI/Swagger documentation,
  and now has manager workflow write/action endpoints. CORS is not implemented.
- React SPA exists in `/frontend` with manager dashboard, order workflow, route calculation,
  Leaflet route comparison, route approval, trips, emissions reports, document archive, profile
  avatar management and administrator pages. Production-like Nginx can serve the built SPA while
  proxying Django API/Admin. Django templates remain available.
- Playwright smoke tests cover local React navigation and role access for demo manager/admin users;
  they require Django, PostgreSQL and `seed_demo` to be prepared before the E2E run.
- GitHub Actions CI covers backend, frontend build and deploy compose validation. Browser E2E is
  intentionally local-only until a dedicated stable CI E2E environment is added.
- Redis, Celery, WebSockets and PostGIS are not implemented.
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
