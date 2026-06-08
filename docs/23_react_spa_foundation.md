# Phase 23 React SPA Foundation

Phase 23 is an architecture and migration-planning phase for moving EcoLogist from a
Django-template user interface to a React single-page application. It records an explicit project
scope change: React is now approved for later phases, while Django, PostgreSQL and the existing
business services remain the backend foundation.

This phase does not add frontend files, API endpoints, migrations or dependencies.

## Target Architecture

```text
Browser
  -> React SPA, React Router, Redux Toolkit, React Leaflet
  -> REST API JSON /api/v1/
  -> Django REST Framework views and serializers
  -> existing Django services and models
  -> PostgreSQL

Browser
  -> OpenStreetMap tile server for Leaflet tiles

Production Docker host
  -> Nginx serves the React build
  -> Nginx proxies /api/, /admin/, protected downloads and /healthz/ to Django/Waitress
  -> Django/Waitress talks to PostgreSQL, optional MinIO and GraphHopper
```

The current Django templates remain available during migration. React replaces the browser-facing
application gradually; it must not rewrite calculation formulas, routing providers, reports,
archive storage or saved route snapshot behavior.

## Stack Decisions

- Frontend: React with Vite and JavaScript.
- Routing: React Router with protected routes based on JWT and user role.
- State and API layer: Redux Toolkit with RTK Query.
- Maps: React Leaflet, preserving internal route geometry as `[[lat, lon], ...]`.
- API: Django REST Framework under `/api/v1/`.
- Auth: existing SimpleJWT Bearer tokens; no OAuth.
- Long-running operations: REST polling first; no WebSocket, Celery, Redis or Channels in the
  initial React phases.
- Development networking: Vite dev proxy to Django to avoid CORS at first.
- Production networking: same-origin Nginx routing, with `/api/` proxied to Django.

## Current State Validation

- The project is on the `phase-23-react-spa-foundation` branch.
- The app is currently a Django monolith with templates, static CSS and small vanilla JS.
- DRF read-only endpoints already exist under `/api/v1/`.
- SimpleJWT endpoints already exist under `/api/v1/auth/`.
- OpenAPI schema, Swagger UI and ReDoc already exist.
- Business API endpoints are still read-only.
- Existing API responses intentionally do not expose route geometry.
- Existing HTML views still use Django sessions.
- Nginx currently serves collected Django static files and proxies all dynamic requests to
  Django/Waitress.

## API Gap Analysis

| Current page/action | Existing API support | Missing API for React | Reuse backend logic | Priority |
|---|---:|---|---|---|
| Login/current user | JWT token, refresh, verify and `/auth/me/` exist | Client logout and refresh error contract | SimpleJWT, `accounts.User` | P0 |
| Manager dashboard | Partial analytics summary exists | Manager counters and recent items endpoint | `ManagerAnalyticsService` and dashboard queries | P0 |
| Locations/transports selects | Read list exists | Optional filtering/search fields | `Location`, `Transport` querysets | P0 |
| Orders list/detail | Read list/detail exists | Pagination/filtering and safe route geometry | Existing manager/admin scoping | P0 |
| Create/edit/cancel order | None | `POST /orders/`, `PATCH /orders/{id}/`, `POST /orders/{id}/cancel/` | Current order form rules extracted to API validation/services | P0 |
| Calculate routes | None | `POST /orders/{id}/calculate-routes/`, optional status endpoint | `RouteCalculationService`, providers | P0 |
| Route comparison map/table | Summary only, no geometry | Route options with `geometry_json`, safe details and warnings | `RouteOption` snapshots and snapshot metrics | P0 |
| Approve route | None | `POST /orders/{id}/routes/{route_option_id}/approve/` | Existing trip creation behavior | P0 |
| Trips list | Read list exists | Trip detail and optional status history | `Trip`, status event queries | P1 |
| Start/deliver trip | None | `POST /trips/{id}/start/`, `POST /trips/{id}/deliver/` | Existing trip status logic | P1 |
| Emissions reports | Analytics summary only | Report filters/results endpoint | `EmissionsReportService` | P1 |
| Document archive | None | Archive list/download/delete endpoints or legacy protected URLs | `DocumentArchiveService` | P2 |
| Admin CRUD | None | Admin users, transports, locations, standards and settings API | Existing admin panel forms/services | P2 |

## Migration Phases

### Phase 24 - Manager API Expansion

- Status: implemented in `docs/24_manager_api_expansion.md`.
- Added DRF write/action endpoints for the manager flow.
- Kept role scoping aligned with the existing HTML views.
- Reused existing services and models for route calculation, route approval, trip lifecycle and
  report data.
- Added tests for permissions, validation, route geometry format, saved snapshots and OpenAPI
  schema.

### Phase 25 - React Scaffold, Auth And Layout

- Create `/frontend` as a Vite React JavaScript app.
- Add React Router, Redux Toolkit, RTK Query and React Leaflet.
- Implement Russian-only login, refresh flow, `/auth/me/`, protected routes and role navigation.
- Store the access token in memory and the refresh token in `sessionStorage`.
- Use a Vite proxy for local API calls.

### Phase 26 - Manager SPA

- Implement manager dashboard, orders, route calculation, comparison map, route approval, trips and
  reports.
- Match the existing user workflow while moving rendering to React.
- Keep existing PDF/XLSX downloads as protected Django URLs until report/archive API scope expands.

### Phase 27 - Admin SPA

- Add the in-application admin dashboard and reference CRUD after the manager flow is stable.
- Keep Django Admin available for extended editing.

### Phase 28 - SPA Deployment

- Build React assets for production.
- Update Nginx to serve the SPA and proxy `/api/`, `/admin/`, protected downloads and `/healthz/`
  to Django.
- Keep Waitress, Django, PostgreSQL and optional MinIO.

### Optional Phase 29 - Background Status Hardening

- Keep polling as the first implementation.
- Add WebSocket or background workers only if measured route calculation or export latency justifies
  the new infrastructure.

## Auth Plan

- React sends `Authorization: Bearer <access_token>` for API calls.
- Access token lives in Redux/RTK Query memory state.
- Refresh token lives in `sessionStorage` and is cleared on logout or refresh failure.
- RTK Query retries one failed request after a successful refresh on `401`.
- If refresh fails, the client clears auth state and redirects to login.
- Existing Django sessions may remain for legacy templates and Django Admin.

## Testing Strategy

- Backend checks remain `.venv\Scripts\python manage.py check`, pytest and `ruff check .`.
- Each new API endpoint needs tests for anonymous rejection, manager/admin scoping, validation
  errors and happy paths.
- Route API tests must assert that geometry uses `[[lat, lon], ...]` and that saved snapshots are
  not recalculated.
- Frontend phases should add Vitest and React Testing Library for auth, reducers, guards, forms and
  RTK Query behavior.
- End-to-end checks should cover login, order creation, route calculation, Leaflet rendering,
  route approval and trip status changes.

## Codex Implementation Rules For Later Phases

- Do not remove Django templates until React parity is verified.
- Do not change database models unless the specific later phase requires it.
- Do not change calculation formulas, route provider contracts, PDF/XLSX generation or archive
  behavior for the React migration itself.
- Keep UI text Russian-only.
- Prefer backend services and DRF serializers over duplicating business rules in React.
- Avoid CORS in the first React phase by using a dev proxy and same-origin production routing.
- Do not add WebSocket, Celery, Redis or Channels before the optional background-status phase.
