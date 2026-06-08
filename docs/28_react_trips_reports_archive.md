# Phase 28 - React Trips, Reports And Archive

## Summary

Phase 28 extends the manager React SPA beyond orders and route comparison:

- `/trips` lists manager trips with status/date filters and Excel export actions.
- `/trips/:id` shows trip detail, route snapshot metrics, lifecycle actions and waybill actions.
- `/reports/emissions` shows the emissions report from Django report services with PDF/XLSX
  download and archive actions.
- `/archive` lists private archived documents with filters, JWT-protected download and delete.

Existing Django templates, Django views, sessions, reports and archive pages remain available.

## Backend API

The phase adds a thin DRF API layer over existing services:

- `GET /api/v1/reports/emissions/pdf/`
- `GET /api/v1/reports/emissions/xlsx/`
- `POST /api/v1/reports/emissions/pdf/archive/`
- `POST /api/v1/reports/emissions/xlsx/archive/`
- `GET /api/v1/trips/export-xlsx/`
- `POST /api/v1/trips/export-xlsx/archive/`
- `GET /api/v1/trips/{id}/waybill/`
- `POST /api/v1/trips/{id}/waybill/archive/`
- `GET /api/v1/reports/archive/`
- `GET /api/v1/reports/archive/{id}/download/`
- `DELETE /api/v1/reports/archive/{id}/`

The endpoints reuse `EmissionsReportService`, `EmissionsReportPdfService`,
`TripExcelExportService`, `WaybillPdfService` and `DocumentArchiveService`.

## Scope Preserved

- No database models changed.
- No migrations added.
- Route providers and calculation formulas are unchanged.
- Saved `RouteOption` snapshots remain the source for report and trip metrics.
- Existing Django-template UI and Django Admin remain available.
- CORS, WebSocket, Celery, Redis, deploy changes and admin SPA remain deferred.

## Frontend

The React SPA now has manager pages for:

- trip list and detail;
- trip start/deliver actions;
- emissions report table and summary cards;
- PDF/XLSX downloads through JWT-authenticated API requests;
- archive list, download and delete.

Access tokens are still attached by RTK Query. File downloads are fetched through the API, converted
to browser object URLs and downloaded without requiring Django session cookies.

## Verification

Expected checks:

```powershell
.venv\Scripts\python manage.py check
.venv\Scripts\python manage.py makemigrations --check --dry-run
.venv\Scripts\python -m pytest --basetemp=.tmp\pytest
.venv\Scripts\python -m ruff check .
cd frontend
npm run build
```
