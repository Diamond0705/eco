# Phase 33 - CI Pipeline And Automated Quality Checks

## Summary

Phase 33 adds GitHub Actions CI for automated quality checks.

The phase does not change application behavior, database models, migrations, route providers,
calculation formulas, report generation, archive behavior, React runtime behavior, Celery, Redis or
WebSockets.

## Workflow

The workflow lives at:

```text
.github/workflows/ci.yml
```

It runs on `push` and `pull_request`.

Jobs:

- `backend` validates Django and Python code.
- `frontend` validates the React production build.
- `deploy-config` validates the production-like compose file.

## Backend CI

The backend job uses:

- Python 3.12, matching the target project stack;
- PostgreSQL 16 as a GitHub Actions service;
- dependencies from `requirements.txt`.

Commands:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python -m pytest --basetemp=.tmp/pytest
python -m ruff check .
```

CI environment values are dummy and safe to commit:

```text
SECRET_KEY=ci-secret-key-not-for-production-keep-it-long
DEBUG=True
DATABASE_URL=postgres://ecologist:ecologist@127.0.0.1:5432/ecologist
ALLOWED_HOSTS=localhost,127.0.0.1,testserver
CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1
USE_S3_STORAGE=False
DOCUMENT_ARCHIVE_ENABLED=True
ROUTE_PROVIDER=mock
GRAPHHOPPER_API_KEY=
GRAPHHOPPER_FALLBACK_TO_MOCK=True
```

The backend CI uses `DEBUG=True` because the existing security tests intentionally verify the local
HTTP development defaults. The deploy config job still validates production-like compose settings
with a dummy `DEBUG=False` value.

The backend CI does not require a real GraphHopper API key and does not require real MinIO/S3.

## Frontend CI

The frontend job uses Node 22 because the current Vite version expects a modern Node runtime.

Commands:

```bash
cd frontend
npm ci
npm run build
```

The job does not run Playwright because the current smoke tests require an already running Django
backend, PostgreSQL, seeded demo users and Vite development server orchestration.

## Deploy Config CI

The deploy config job creates a dummy `.env` file for compose interpolation and runs:

```bash
docker compose -f docker-compose.deploy.yml config
```

It validates the deploy configuration shape without building images, pulling all services or
requiring production secrets.

## Local Reproduction

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
```

Deploy config:

```powershell
docker compose -f docker-compose.deploy.yml config
```

Local E2E smoke:

```powershell
docker compose up -d db minio
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py seed_demo
.venv\Scripts\python.exe manage.py runserver
cd frontend
npm.cmd run test:e2e
```

## Out Of Scope

- No real GraphHopper calls in CI.
- No real MinIO/S3 dependency in CI.
- No browser E2E job in CI yet.
- No production image build in CI yet.
- No secrets committed to the repository.
