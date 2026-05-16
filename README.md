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

Routing currently uses deterministic mock data only. A real routing provider is planned for
Phase 8 and must be added behind the existing provider boundary so orders, trips, reports and
analytics continue to consume saved `RouteOption` snapshots.

## Stack

- Python 3.12 target, Python 3.14.4 allowed locally inside `.venv`
- Django 5.2 LTS
- PostgreSQL 16
- Django ORM and migrations
- Django templates + project CSS / Bootstrap-style layout
- Leaflet
- ReportLab
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

Run checks:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
pytest
ruff check .
```

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

## Current Limitations

- Routing uses only deterministic mock geometry.
- GraphHopper integration is planned as a future extension.
- No real traffic, roadworks, truck restrictions or GPS tracking.
- No Excel export.
- No production deployment setup.
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

Do not add FastAPI, React, Celery, Redis, MinIO, S3, PostGIS, Nginx, WebSocket, real GPS tracking, Excel export, arbitrary address geocoding, or strict EN 16258 / EMEP / EEA calculations unless the project scope is explicitly changed.
