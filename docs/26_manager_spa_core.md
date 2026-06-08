# Phase 26 Manager SPA Core

Phase 26 implements the first real manager workflow in the React SPA. The frontend now uses the
Phase 24 manager API for dashboard and order operations while Django templates remain available.

This phase does not change Django views, backend business logic, database models, migrations,
calculation formulas, routing providers, PDF/XLSX/archive logic, CORS, WebSocket, Celery, Redis or
admin React pages.

## Implemented React Pages

- `/dashboard` - manager dashboard backed by `GET /api/v1/manager/dashboard/`.
- `/orders` - orders list backed by `GET /api/v1/orders/`.
- `/orders/create` - order creation form backed by `POST /api/v1/orders/`.
- `/orders/:id` - order detail backed by `GET /api/v1/orders/<id>/`.

The order detail page can cancel eligible orders through
`POST /api/v1/orders/<id>/cancel/`.

## API Usage

Phase 26 adds `frontend/src/api/managerApi.js` with RTK Query hooks for:

- manager dashboard summary;
- orders list;
- order detail;
- order create;
- order cancel;
- transports list;
- locations list.

The React app keeps using the Phase 25 JWT strategy: access token in memory, refresh token in
`sessionStorage`, Bearer authorization header and refresh-on-401 retry.

## UI Components

The phase adds small project-native UI components instead of a component library:

- `PageShell`;
- `Card`;
- `Button`;
- `Badge`;
- `DataTable`;
- `FormField`;
- `Alert`;
- `EmptyState`;
- `LoadingState`.

No MUI, Ant Design, Tailwind, Bootstrap, FontAwesome or other heavy UI dependency is introduced.

## UX Scope

- Russian UI only.
- EcoLogist green palette and existing logo/static images.
- Compact dashboard cards for orders, active trips, delivered trips and CO2.
- Orders table with a client-side status filter.
- Create form uses API transports and locations.
- Transport helper shows capacity and whether the selected transport fits the entered cargo weight.
- Detail page shows cargo, transport, delivery date, notes, route points and available actions.
- Route calculation UI and Leaflet route comparison are deferred to the next phase.
- Admin SPA remains deferred.

## Checks

Phase 26 should pass:

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.venv\Scripts\python.exe -m pytest --basetemp=.tmp\pytest
.venv\Scripts\python.exe -m ruff check .
cd frontend
npm.cmd install
npm.cmd run build
```
