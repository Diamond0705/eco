# Phase 35 - React Manager UI Template Parity

## Summary

Phase 35 aligns the manager React SPA with the existing Django-template visual language.

The phase is frontend-only. It does not change backend APIs, models, migrations, calculations,
routing providers, Django templates, Django Admin, dependencies or deploy logic.

## Manager UI Changes

- Manager React now uses the Django-template style white top navigation with the EcoLogist logo.
- The manager workspace uses `dashboard-background.png`, broad translucent panels, green links,
  soft shadows and compact rounded cards.
- `/dashboard` follows `manager_dashboard.html`: four metric cards, circular icons, route/report
  feature cards, existing manager illustrations and footer line.
- `/orders/create` follows `order_create.html`: large form panel with cargo, transport and route
  sections.
- `/archive` follows `archive.html`: filter card, date range controls, document file icons,
  format badges and separate download/delete actions.
- Other manager pages reuse the same panel, card, table, form, button and alert styling.
- `/analytics` is added as a lightweight manager React route backed by the existing dashboard API
  data, so the manager top navigation matches Django templates.

## Out Of Scope

- No admin-specific React redesign.
- No backend endpoint changes.
- No new dependencies.
- No business logic changes.
- No changes to route calculations, reports, document archive services or saved snapshots.

## Verification

Run:

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.venv\Scripts\python.exe -m pytest --basetemp=.tmp\pytest
.venv\Scripts\python.exe -m ruff check .
cd frontend
npm.cmd install
npm.cmd run build
npm.cmd run test:e2e
```

Visual smoke:

- `/dashboard`
- `/orders`
- `/orders/create`
- `/analytics`
- `/archive`
- `/reports/emissions`
- `/profile`

Check desktop and mobile widths. The top navigation should wrap cleanly, tables should scroll
horizontally when needed, forms should stay inside panels and the route map should remain visible.
