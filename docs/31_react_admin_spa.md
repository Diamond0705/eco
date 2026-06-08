# Phase 31 - React Admin SPA

## Summary

Phase 31 adds the first React implementation of the in-application administrator panel.

The Django backend remains the source of truth. Existing Django templates and Django Admin remain
available; React uses JSON REST endpoints under `/api/v1/admin/`.

## Backend API

New admin-only endpoints:

- `GET /api/v1/admin/dashboard/`
- `GET /api/v1/admin/dashboard/export-xlsx/`
- `POST /api/v1/admin/dashboard/export-xlsx/archive/`
- `GET /api/v1/admin/users/`
- `GET /api/v1/admin/users/<id>/`
- `PATCH /api/v1/admin/users/<id>/`
- `GET /api/v1/admin/transports/`
- `POST /api/v1/admin/transports/`
- `GET /api/v1/admin/transports/<id>/`
- `PATCH /api/v1/admin/transports/<id>/`
- `GET /api/v1/admin/locations/`
- `POST /api/v1/admin/locations/`
- `GET /api/v1/admin/locations/<id>/`
- `PATCH /api/v1/admin/locations/<id>/`
- `GET /api/v1/admin/eco-standards/`
- `POST /api/v1/admin/eco-standards/`
- `GET /api/v1/admin/eco-standards/<id>/`
- `PATCH /api/v1/admin/eco-standards/<id>/`
- `GET /api/v1/admin/calculation-settings/`
- `POST /api/v1/admin/calculation-settings/`

Only admins and superusers can use these endpoints. Managers receive `403`; anonymous requests
receive `401`.

`GET /api/v1/auth/me/` now includes derived `is_admin`, used by React route guards. It does not
replace Django permissions or expose password hashes.

## Frontend

React adds a separate administrator layout with top navigation and the existing EcoLogist visual
direction:

- `/admin/dashboard`
- `/admin/archive`
- `/admin/users`
- `/admin/transports`
- `/admin/locations`
- `/admin/eco-standards`
- `/admin/calculation-settings`
- `/admin/profile`

The admin layout reuses:

- `/static/img/ecologist-truck-mark.png`
- `/static/img/dashboard-background.png`
- RTK Query, React Router and the existing JWT auth flow.

User management is intentionally limited to activity changes for manager accounts. Role changes,
password changes, staff flags and superuser controls remain in Django Admin.

Calculation settings are saved as new active versions. Existing route snapshots are not
recalculated.

## Deployment

Nginx keeps `/admin/` proxied to Django Admin.

Selected React admin routes under `/admin/...` use the SPA fallback, so production can serve both
the React admin panel and Django Admin without moving Django Admin to another URL.

## Verification

Expected checks:

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.venv\Scripts\python.exe -m pytest --basetemp=.tmp\pytest
.venv\Scripts\python.exe -m ruff check .
cd frontend
npm.cmd run build
```

Phase 31 does not add migrations, new background workers, WebSockets, Redis, Celery, CORS or
changes to calculations, route providers, reports or archive services.
