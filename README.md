# EcoLogist

EcoLogist is an educational Django monolith for planning road freight transportation with simplified environmental impact calculation.

The MVP UI is Russian-only. The demo domain is Russia-oriented: RUB currency, diesel fuel price in RUB/liter, Moscow and Moscow Oblast locations, and the `Europe/Moscow` timezone.

## MVP Status

The MVP is completed through Phase 7:

- accounts, registration, login/logout, profile and role-based dashboards;
- fleet, eco standards, calculation settings and demo locations;
- shipment orders with route points and status workflow;
- mock route calculation, route comparison and Leaflet map;
- route approval, Trip lifecycle and status history;
- PDF waybill and emissions PDF via ReportLab;
- manager analytics, admin company dashboard and final UI polish.

Routing defaults to deterministic mock data. Phase 8 adds optional GraphHopper routing behind
the existing provider boundary so orders, trips, reports and analytics continue to consume saved
`RouteOption` snapshots. Phase 13 adds Calculation Model v2.1 for new calculations: routes above
`MAX_ROUTE_DISTANCE_KM` are filtered or rejected, eco-rating uses educational emissions intensity,
and absolute emissions remain saved as route snapshots. Phase 15 adds in-application administrator
CRUD pages for common management tasks while keeping Django Admin available for extended editing.

## Stack

- Python 3.12 target, Python 3.14.4 allowed locally inside `.venv`
- Django 5.2 LTS
- PostgreSQL 16
- Django ORM and migrations
- Django templates + project CSS / Bootstrap-style layout
- Leaflet
- ReportLab
- openpyxl for synchronous `.xlsx` exports
- django-storages with S3 support for the optional private document archive
- Django REST Framework for the read-only session-authenticated API
- SimpleJWT for external Bearer-token API authentication
- Waitress for deployment WSGI serving
- pytest + pytest-django
- ruff

## Local Setup

```powershell
py -3.14 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
docker compose up -d db
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Optional local MinIO for the private document archive:

```powershell
docker compose up -d minio
```

Open `http://localhost:9001`, log in with `AWS_ACCESS_KEY_ID` /
`AWS_SECRET_ACCESS_KEY` from `.env`, and create the private bucket
`ecologist-documents`. Keep `USE_S3_STORAGE=False` for plain local file storage,
or set it to `True` to store archived documents in MinIO. Archived PDF/XLSX files
are still downloaded through authorized Django views and are not exposed as public
MinIO URLs.

For normal test runs, keep `USE_S3_STORAGE=False` or rely on the test suite override:
pytest uses local temporary file storage and does not require real MinIO/S3. Set
`USE_S3_STORAGE=True` only for manual MinIO checks after starting the local MinIO service.
When running Django from `.venv`, use `AWS_S3_ENDPOINT_URL=http://localhost:9000`.
When running Django inside `docker-compose.deploy.yml`, the compose file overrides the endpoint to
`http://minio:9000`.

Routing provider settings:

```powershell
ROUTE_PROVIDER=mock
CALCULATION_MODEL=v2.1
MAX_ROUTE_DISTANCE_KM=2000
GRAPHHOPPER_API_KEY=
GRAPHHOPPER_BASE_URL=https://graphhopper.com/api/1
GRAPHHOPPER_PROFILE=car
GRAPHHOPPER_TIMEOUT_SECONDS=10
GRAPHHOPPER_FALLBACK_TO_MOCK=True
GRAPHHOPPER_ALTERNATIVE_MAX_PATHS=5
GRAPHHOPPER_ALTERNATIVE_MAX_WEIGHT_FACTOR=1.6
GRAPHHOPPER_ALTERNATIVE_MAX_SHARE_FACTOR=0.7
GRAPHHOPPER_TARGET_CANDIDATES=3
GRAPHHOPPER_MAX_CANDIDATES=5
GRAPHHOPPER_ENABLE_STRATEGY_REQUESTS=False
GRAPHHOPPER_MAX_STRATEGY_REQUESTS=2
```

Run checks:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
pytest
ruff check .
```

## Deployment Prep

Local Windows development still uses Django `runserver`. For production-style deployment, Phase 18
adds a separate Docker/Nginx path:

```powershell
docker compose -f docker-compose.deploy.yml up -d --build
docker compose -f docker-compose.deploy.yml exec web python manage.py migrate
```

The deploy stack uses Nginx + Waitress + Django + PostgreSQL + MinIO. Gunicorn is intentionally
not used. The web container runs:

```powershell
waitress-serve --listen=0.0.0.0:8000 config.wsgi:application
```

Set production security variables in `.env` before `DEBUG=False`:

```env
SECRET_KEY=replace-with-a-long-random-secret
ALLOWED_HOSTS=example.com,www.example.com
CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
USE_X_FORWARDED_PROTO=True
```

The deploy entrypoint runs `python manage.py collectstatic --noinput`. Nginx serves collected
`/static/` files and proxies dynamic requests to Django. Private archived PDF/XLSX files are not
served by Nginx or public MinIO URLs; downloads still go through authorized Django views.

In `docker-compose.deploy.yml`, MinIO ports are published for local Phase 18 verification, so the
console is available at `http://localhost:9001` after:

```powershell
docker compose -f docker-compose.deploy.yml up -d --build
```

Create the private bucket `ecologist-documents` manually before checking archive saves with
`USE_S3_STORAGE=True`. Do not expose MinIO publicly in production unless a separate private
network and access policy have been designed; close these ports or move them to a local-only
override for real production use.

Manual PostgreSQL backup:

```powershell
docker compose -f docker-compose.deploy.yml exec db pg_dump -U ecologist -d ecologist -Fc -f /tmp/ecologist.dump
docker compose -f docker-compose.deploy.yml cp db:/tmp/ecologist.dump .\ecologist.dump
```

Manual restore:

```powershell
docker compose -f docker-compose.deploy.yml cp .\ecologist.dump db:/tmp/ecologist.dump
docker compose -f docker-compose.deploy.yml exec db pg_restore -U ecologist -d ecologist --clean --if-exists /tmp/ecologist.dump
```

This is deployment preparation, not a full managed VPS/cloud setup: TLS automation, monitoring and
scheduled backups remain future work.

## Demo Users

The `seed_demo` command creates:

- administrator: `admin_demo` / `Admin12345!`
- manager: `manager_demo` / `Manager12345!`

## Demo Scenario

1. Log in as `manager_demo`.
2. Create a shipment order with two demo locations.
3. Calculate mock route options.
4. Compare routes by distance, cost, emissions and eco-rating.
5. Approve one route to create a Trip.
6. Start and deliver the Trip.
7. Download the waybill PDF.
8. Open emissions reports and analytics.
9. Download Excel exports for emissions, analytics or trip lists.

## Read-Only API

Phase 19 adds a small JSON API under `/api/v1/` for authenticated integrations:

- `GET /api/v1/locations/`
- `GET /api/v1/transports/`
- `GET /api/v1/orders/`
- `GET /api/v1/orders/<id>/`
- `GET /api/v1/trips/`
- `GET /api/v1/analytics/summary/`

The API supports Django session authentication for browser users and JWT Bearer tokens for
external clients. It is read-only: write methods return `405`. CORS and Swagger/OpenAPI UI are
intentionally not added. See `docs/19_rest_api.md` and `docs/20_jwt_api_auth.md` for endpoint,
token and data exposure rules.

Token endpoints:

- `POST /api/v1/auth/token/`
- `POST /api/v1/auth/token/refresh/`
- `POST /api/v1/auth/token/verify/`
- `GET /api/v1/auth/me/`

Use `Authorization: Bearer <access_token>` for API calls. In production, use JWT only over HTTPS.

## Current Limitations

- Mock routing returns three deterministic demo routes.
- GraphHopper routing returns the real alternatives available from the provider and does not
  duplicate routes to force three options.
- Standard GraphHopper calculation requests up to 3 routes; extended calculation requests up to
  5 routes and may try best-effort strategy requests.
- The best eco route is determined after calculation from stored route facts and settings.
- Excel exports are generated synchronously from saved route snapshots and are not stored.
- Generated PDF/XLSX files can optionally be saved to the private document archive.
- No real traffic, roadworks, truck restrictions or GPS tracking.
- Production-style Docker/Nginx deployment preparation is available; full managed hosting,
  TLS automation and scheduled backups are not implemented.
- The REST API is read-only and supports sessions plus JWT Bearer tokens; write API, CORS and
  Swagger/OpenAPI UI are not implemented.
- Environmental formulas are simplified for education and are not a strict EN 16258, EMEP or EEA implementation.

## Current Documentation

`docs/08_current_state.md` is the current implementation snapshot. Earlier docs in `docs/00_*`
through `docs/07_*` are useful historical and planning notes and may still describe earlier
phase boundaries.

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

## MVP Boundaries

Do not add FastAPI, React, Celery, Redis, PostGIS, WebSocket, real GPS tracking, arbitrary address geocoding, or strict EN 16258 / EMEP / EEA calculations unless the project scope is explicitly changed. MinIO/S3-compatible storage is limited to the approved Phase 17 private document archive. Nginx and Waitress are limited to the approved Phase 18 deployment path. Excel export is limited to the approved synchronous `.xlsx` downloads.
Django REST Framework is limited to the approved read-only API. SimpleJWT is limited to the
approved Phase 20 external API authentication endpoints; CORS, OAuth, Swagger/OpenAPI UI and write
API remain out of scope.
