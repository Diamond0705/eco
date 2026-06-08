# Phase 27 React Route Comparison And Approval

Phase 27 adds route calculation, route comparison and route approval to the React manager SPA.
The React app still uses Django REST API responses as the source of truth and does not call
GraphHopper or any routing provider directly.

This phase does not remove Django templates, change Django views, change database models, create
migrations, change calculation formulas, change routing providers, change PDF/XLSX/archive logic,
add admin React pages, add CORS, add WebSocket, add Celery or add Redis.

## Frontend Scope

- Adds `/orders/:id/routes`.
- Adds route calculation action from the order detail page.
- Adds route comparison page with order summary, route points, Leaflet map and route option cards.
- Adds route approval action through the existing manager API.
- Adds React Leaflet and Leaflet frontend dependencies.

Trips, reports, document archive and admin React pages remain future phases.

## API Usage

Phase 27 extends `frontend/src/api/managerApi.js` with:

- `POST /api/v1/orders/<id>/calculate-routes/`;
- `GET /api/v1/orders/<id>/route-options/`;
- `POST /api/v1/orders/<order_id>/routes/<route_option_id>/approve/`.

The route page also uses the existing order detail endpoint:

- `GET /api/v1/orders/<id>/`.

Route approval reuses `TripLifecycleService` through the backend API. React does not duplicate
trip creation logic.

## Map Strategy

- React Leaflet renders saved `geometry_json` only.
- Internal route geometry remains `[[lat, lon], ...]`.
- OpenStreetMap tiles remain the browser-facing tile source.
- The map fits bounds to returned route alternatives when geometry exists.
- Start and destination markers are rendered with local Leaflet `divIcon` markers to avoid extra
asset handling for default marker images.

## Route Option Display

Each route option card shows:

- provider/source;
- route badges from the backend;
- платная дорога badge when the route has unpriced tolls;
- distance, duration, fuel, cost, CO2, NOx, PM and eco rating;
- warnings;
- collapsible calculation summary.

Backend-provided badge and calculation data are displayed without recalculating saved route
snapshots in React.

## Approval Flow

- Managers click `Утвердить` on a route option.
- React calls the approve endpoint.
- Backend creates the trip and marks the selected route.
- React navigates back to the order detail page with a success message containing the created trip
  id.

## Checks

Phase 27 should pass:

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.venv\Scripts\python.exe -m pytest --basetemp=.tmp\pytest
.venv\Scripts\python.exe -m ruff check .
cd frontend
npm.cmd install
npm.cmd run build
```
