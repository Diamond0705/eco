# Phase 32 - React UI Stabilization And E2E Smoke Tests

## Summary

Phase 32 adds lightweight end-to-end smoke coverage for the completed React SPA.

The tests focus on demo readiness and route stability. They do not add business features, change
calculation formulas, change route providers, alter database models or replace Django templates.

## Playwright Setup

The frontend now uses Playwright through `@playwright/test`.

Frontend scripts:

```powershell
cd frontend
npm.cmd run test:e2e
npm.cmd run test:e2e:headed
npm.cmd run test:e2e:ui
```

The Playwright config starts Vite on `http://127.0.0.1:5174` and reuses an existing Vite server if
one is already running.

Django is intentionally not started by Playwright. Before running E2E tests, start the backend and
seed demo data:

```powershell
docker compose up -d db minio
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py seed_demo
.venv\Scripts\python.exe manage.py runserver
```

Default demo credentials:

- manager: `manager_demo` / `Manager12345!`
- administrator: `admin_demo` / `Admin12345!`

They can be overridden with:

```powershell
$env:ECOLOGIST_MANAGER_USERNAME="manager_demo"
$env:ECOLOGIST_MANAGER_PASSWORD="Manager12345!"
$env:ECOLOGIST_ADMIN_USERNAME="admin_demo"
$env:ECOLOGIST_ADMIN_PASSWORD="Admin12345!"
$env:ECOLOGIST_BACKEND_URL="http://127.0.0.1:8000"
$env:PLAYWRIGHT_BASE_URL="http://127.0.0.1:5174"
```

If Playwright browser binaries are missing, install Chromium:

```powershell
cd frontend
npx playwright install chromium
```

## Smoke Coverage

Manager smoke checks:

- anonymous `/dashboard` redirects to `/login`;
- manager can log in;
- manager can open dashboard, orders, create order, trips, emissions reports, archive and profile;
- manager cannot open `/admin/dashboard`.

Administrator smoke checks:

- administrator can log in;
- administrator can open dashboard, archive, users, transports, locations, eco standards,
  calculation settings and profile;
- Django Admin is still reachable on the backend at `/admin/`.

## Out Of Scope

- No full visual regression.
- No real GraphHopper dependency.
- No end-to-end order creation or route calculation in this phase.
- No Docker/PostgreSQL lifecycle inside Playwright.
- No Celery, Redis, WebSocket, PostGIS, monitoring or production observability.
