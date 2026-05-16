# AGENTS.md - EcoLogist

## Project

EcoLogist is an educational Django web application for planning road freight transportation with simplified environmental impact calculation.

The UI language is Russian only. Do not add an English UI or an i18n language switch in the MVP.

The project is oriented to Russia: Russian UI, RUB currency, diesel fuel price in RUB/liter, Moscow and Moscow Oblast demo locations, and `Europe/Moscow` timezone.

## Fixed Stack

Target stack from the source technical brief:

- Python 3.12
- Django 5.2 LTS
- PostgreSQL 16
- Django ORM and migrations
- Django templates
- project CSS / Bootstrap-style layout
- Leaflet
- ReportLab
- pytest + pytest-django
- ruff

Local development note: Python 3.14.4 is allowed only inside `.venv` with `Django>=5.2.8,<5.3`. Always use `.venv`. Do not install packages globally.

## Do Not Use In MVP

Do not add these technologies unless the user explicitly changes the scope:

- FastAPI
- React
- Celery
- Redis
- MinIO
- S3
- PostGIS
- Nginx
- WebSocket
- real GPS tracking
- Excel export
- arbitrary address geocoding
- strict EN 16258 / EMEP / EEA implementation

## Critical Start Rule: Custom User

Create `accounts.User` before the first migrations.

`accounts.User` must inherit from `django.contrib.auth.models.AbstractUser`.

Fields to add:

- `middle_name`
- `phone`
- `role`

Roles:

- `manager`
- `admin`

`settings.py` must contain:

```python
AUTH_USER_MODEL = "accounts.User"
```

All foreign keys to users must use `settings.AUTH_USER_MODEL` or `get_user_model()`. Do not import `django.contrib.auth.models.User` directly.

## Routing Rules

The first version uses `MockRouteProvider` only.

`MockRouteProvider` must not call external APIs. It builds `distance_km`, `duration_minutes`, `geometry_json`, and `fuel_multiplier` from predefined `Location` coordinates.

Leaflet draws `geometry_json` as polylines. Internal `geometry_json` format is always `[[lat, lon], ...]`.

Future `GraphHopperRouteProvider` must be isolated and must return the same internal `RouteCandidate` format. Do not pass raw external API responses to views, templates, reports, or analytics.

## RouteCandidate / RouteOption Rules

`RouteCandidate` may have automatic `fuel_multiplier` set by the provider.

Do not use a manually entered `route_factor` in the MVP.

Recommended mock `fuel_multiplier` values:

- `fast = 1.08`
- `short = 1.00`
- `eco = 0.92`

`RouteOption` must store calculated values as a snapshot:

- `distance_km`
- `duration_minutes`
- `fuel_multiplier`
- `fuel_liters`
- `cost_rub`
- `co2_kg`
- `nox_g`
- `pm_g`
- `eco_rating`
- `geometry_json`

Old `RouteOption` values must not be recalculated automatically when settings change. If practical, `RouteOption` should store a reference to the `EcoCalculationSettings` record used during calculation.

## EcoCalculationSettings Singleton

`EcoCalculationSettings` may contain several records for history, but only one record may be active.

All calculations must call `EcoCalculationSettings.get_current()`.

If a new active settings record is saved, other active records must be deactivated.

Changing settings affects new calculations only.

## Default Seed Values

- `diesel_co2_kg_per_liter = 2.69`
- Euro III: NOx `5.00 g/kWh`, PM `160 mg/kWh`
- Euro IV: NOx `3.50 g/kWh`, PM `30 mg/kWh`
- Euro V: NOx `2.00 g/kWh`, PM `30 mg/kWh`
- Euro VI: NOx `0.46 g/kWh`, PM `10 mg/kWh`
- `engine_work_kwh_per_km = 1.20`
- `fuel_price_rub_per_liter = 78.15`
- `service_tariff_rub_per_km = 175.00`
- `full_load_fuel_increase_percent = 20.00`
- `co2_weight / nox_weight / pm_weight = 0.50 / 0.30 / 0.20`
- `co2_critical_kg / nox_critical_g / pm_critical_g = 100 / 300 / 10`

## Commands

```powershell
py -3.14 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
docker compose up -d db
python manage.py check
python manage.py makemigrations
python manage.py migrate
pytest
ruff check .
```

Do not run `git init` unless the user asks.

## Definition Of Done

A task is done only when:

- requested feature works
- migrations are created if models changed
- Russian UI labels are present
- tests are added or existing tests pass
- no unrelated architecture changes were made
- no forbidden MVP technologies were added
- the project still runs with `python manage.py runserver`
- the answer includes changed files and verification result
