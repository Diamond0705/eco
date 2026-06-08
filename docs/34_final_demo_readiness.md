# Phase 34 - Final Demo Readiness And Documentation Alignment

## Summary

Phase 34 prepares EcoLogist for final demonstration.

It does not add business features, migrations, dependencies, Redis, Celery, WebSockets, PostGIS,
formula changes, routing provider changes, React behavior changes or deploy logic changes.

## Final Architecture

```text
Browser
  -> React SPA served by Vite in development or Nginx in deploy mode
  -> REST API JSON under /api/v1/
  -> Django REST Framework views and serializers
  -> existing Django services/models
  -> PostgreSQL

Browser
  -> OpenStreetMap tile server for Leaflet map tiles

Nginx deploy mode
  -> serves React build
  -> proxies /api/, /admin/, /healthz/ and protected backend routes to Django/Waitress
  -> serves collected static files

Django
  -> MinIO/S3-compatible storage for protected documents and avatars when enabled
  -> GraphHopper API when real routing is enabled
```

React SPA is the main user-facing interface. Django templates remain available as
legacy/fallback/internal views. Django Admin remains available at `/admin/`.

## Final Stack

Backend:

- Python
- Django
- Django REST Framework
- SimpleJWT
- PostgreSQL
- MinIO/S3-compatible storage
- ReportLab
- openpyxl
- GraphHopper integration

Frontend:

- React
- Vite
- JavaScript
- React Router
- Redux Toolkit
- RTK Query
- React Leaflet
- HTML/CSS

Infrastructure and quality:

- Docker Compose
- Nginx
- Waitress
- GitHub Actions CI
- Playwright
- pytest
- ruff

Not implemented:

- Redis
- Celery
- WebSockets
- PostGIS

These remain future options only.

## Local Development Demo

Start services and backend:

```powershell
docker compose up -d db minio
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py seed_demo
.venv\Scripts\python.exe manage.py runserver
```

Start the React SPA in a second terminal:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Open the Vite URL, usually:

```text
http://127.0.0.1:5173/
```

Keep Django running on:

```text
http://127.0.0.1:8000/
```

Vite proxies `/api` and `/static` to Django, so CORS is not required for the local demo.

## Production-Like Deploy Demo

Build and start the deploy stack:

```powershell
docker compose -f docker-compose.deploy.yml up -d --build
docker compose -f docker-compose.deploy.yml exec web python manage.py migrate
docker compose -f docker-compose.deploy.yml exec web python manage.py seed_demo
```

Open:

```text
http://localhost/
```

Smoke checks:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost/
Invoke-WebRequest -UseBasicParsing http://localhost/login
Invoke-WebRequest -UseBasicParsing http://localhost/healthz/
Invoke-WebRequest -UseBasicParsing http://localhost/api/v1/auth/me/
Invoke-WebRequest -UseBasicParsing http://localhost/admin/
Invoke-WebRequest -UseBasicParsing http://localhost/admin/dashboard
```

Expected:

- `/` and React routes return the SPA.
- `/api/v1/auth/me/` reaches Django and returns `401` for anonymous requests.
- `/healthz/` returns `ok`.
- `/admin/` opens Django Admin.
- `/admin/dashboard` opens the React administrator route.

Stop deploy stack:

```powershell
docker compose -f docker-compose.deploy.yml down
```

## Demo Users

`seed_demo` creates or updates:

- administrator: `admin_demo` / `Admin12345!`
- manager: `manager_demo` / `Manager12345!`

## Manager Demo Flow

1. Log in as `manager_demo`.
2. Open the manager dashboard.
3. Open orders.
4. Create a shipment order using demo locations and transport.
5. Calculate route options.
6. Compare distance, duration, cost, emissions and eco rating.
7. Review the route geometry on the Leaflet map.
8. Approve one route.
9. Open the created trip.
10. Start and deliver the trip if the scenario needs the full lifecycle.
11. Open emissions reports.
12. Download PDF/XLSX documents.
13. Save a report or waybill to the archive.
14. Open the archive and download the saved document.
15. Open profile and demonstrate avatar upload/delete if needed.

## Admin Demo Flow

1. Log in as `admin_demo`.
2. Open the React admin dashboard.
3. Show company counters and top lists.
4. Open users and toggle active status on a safe non-admin demo user if needed.
5. Open transports.
6. Open locations.
7. Open eco standards.
8. Open calculation settings and explain that new settings affect new calculations only.
9. Open the admin archive.
10. Open the Django Admin link and verify `/admin/` remains available.

## API Demo

Open API documentation:

```text
http://127.0.0.1:8000/api/schema/
http://127.0.0.1:8000/api/docs/
http://127.0.0.1:8000/api/redoc/
```

Obtain JWT:

```http
POST /api/v1/auth/token/
```

Call current user:

```http
GET /api/v1/auth/me/
Authorization: Bearer <access_token>
```

The OpenAPI schema at `/api/schema/` can be imported into Postman. In Swagger, use the Authorize
button with:

```text
Bearer <access_token>
```

The API is used by the React SPA. Django services and models remain the source of truth.

## Demo Data Reset

Create or refresh demo data:

```powershell
.venv\Scripts\python.exe manage.py seed_demo
```

Clear operational demo data while preserving users and reference data:

```powershell
.venv\Scripts\python.exe manage.py clear_operational_data --yes
```

Clear operational data and reset operational table sequences:

```powershell
.venv\Scripts\python.exe manage.py clear_operational_data --yes --reset-sequences
```

The cleanup command deletes orders, order points, route options, trips and trip status events. It
does not delete users, transports, locations, eco standards, calculation settings, groups or
permissions.

Do not commit runtime artifacts:

- `.env`
- `.tmp/`
- `.pytest_cache/`
- `.ruff_cache/`
- `frontend/node_modules/`
- `frontend/dist/`
- `frontend/playwright-report/`
- `frontend/test-results/`
- `media/` generated files
- `protected_media/` generated protected documents and avatars

## Security Notes

- Passwords are stored through Django password hashing, never in plain text.
- React uses JWT Bearer tokens for API requests.
- Django sessions remain for Django Admin and legacy/template views.
- Production settings support secure cookies, SSL redirect, HSTS and forwarded HTTPS headers.
- Protected documents and avatars are served through authorized Django/API endpoints, not public
  MinIO URLs.
- `.env` and real GraphHopper/S3/Django secrets must not be committed.
- The project documents technical measures only and does not claim legal certification.

## Verification Commands

Backend:

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.venv\Scripts\python.exe -m pytest --basetemp=.tmp\pytest
.venv\Scripts\python.exe -m ruff check .
```

Frontend:

```powershell
cd frontend
npm.cmd install
npm.cmd run build
npm.cmd run test:e2e
```

Deploy:

```powershell
docker compose -f docker-compose.deploy.yml config
```

CI:

- GitHub Actions runs on `push` and `pull_request`.
- After pushing the branch, check the backend, frontend and deploy-config jobs.
