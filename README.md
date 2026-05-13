# EcoLogist

EcoLogist is an educational Django web application for planning road freight transportation with simplified environmental impact calculation.

The UI is Russian-only. The MVP is oriented to Russia: RUB currency, diesel fuel price in RUB/liter, demo locations in Moscow and Moscow Oblast, and `Europe/Moscow` timezone.

## Stack

Target stack from the project brief:

- Python 3.12
- Django 5.2 LTS
- PostgreSQL 16
- Django ORM and migrations
- Django templates
- Bootstrap 5
- Leaflet
- ReportLab
- pytest + pytest-django
- ruff

Local development note: this workspace uses Python 3.14.4 inside `.venv`. This is acceptable with `Django>=5.2.8,<5.3`, because Django 5.2.8+ supports Python 3.14.

Always use `.venv`. Do not install packages globally.

## Local Setup

Create and activate the virtual environment:

```powershell
py -3.14 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Create local environment settings:

```powershell
Copy-Item .env.example .env
```

Start PostgreSQL:

```powershell
docker compose up -d db
```

Run Django checks and migrations:

```powershell
python manage.py check
python manage.py makemigrations
python manage.py migrate
```

Run the development server:

```powershell
python manage.py runserver
```

Run tests and linting:

```powershell
pytest
ruff check .
```

## MVP Boundaries

Do not add FastAPI, React, Celery, Redis, MinIO, S3, PostGIS, Nginx, WebSocket, real GPS tracking, Excel export, arbitrary address geocoding, or strict EN 16258 / EMEP / EEA calculations in the MVP.

Phase 0 contains only the initial Django monolith skeleton, custom user model, documentation, settings, and smoke tests. Orders, routing, trips, reports, PDF generation, and eco calculations are intentionally not implemented yet.
