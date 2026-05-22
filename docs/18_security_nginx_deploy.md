# Phase 18 Security And Nginx Deploy Prep

Phase 18 prepares EcoLogist for a production-style Docker deployment while keeping local Windows
development unchanged.

## Local Development

Local development still uses:

```powershell
.venv\Scripts\python.exe manage.py runserver
```

The local defaults keep HTTP working on `127.0.0.1:8000`: secure cookies, HSTS and SSL redirect
are disabled unless enabled through `.env`.

For regular tests, keep `USE_S3_STORAGE=False`. The pytest configuration also forces local
temporary file storage so tests do not require real MinIO/S3 even if a developer temporarily sets
`USE_S3_STORAGE=True` in `.env`.

## Deploy Stack

The deployment stack is:

- Nginx reverse proxy;
- Django served by Waitress;
- PostgreSQL 16;
- MinIO/S3-compatible private document archive.

Gunicorn is not used in this phase because the target deployment path is Windows-friendly and
Waitress is the selected WSGI application server.

## Required Environment

Set production values before running with `DEBUG=False`:

```env
DEBUG=False
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

For MinIO-backed document archive in deploy compose:

```env
USE_S3_STORAGE=True
AWS_ACCESS_KEY_ID=replace-me
AWS_SECRET_ACCESS_KEY=replace-me
AWS_STORAGE_BUCKET_NAME=ecologist-documents
AWS_S3_ENDPOINT_URL=http://minio:9000
AWS_S3_REGION_NAME=us-east-1
AWS_S3_ADDRESSING_STYLE=path
```

For local `.venv` runserver checks, use `AWS_S3_ENDPOINT_URL=http://localhost:9000`.
`docker-compose.deploy.yml` overrides the web container endpoint to `http://minio:9000`, because
service names are resolved inside the Docker network.

Blank `ALLOWED_HOSTS` falls back to safe local defaults, and blank `CSRF_TRUSTED_ORIGINS` becomes
an empty list. For local browser work, recommended values are:

```env
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1
```

## Static And Private Files

The deploy entrypoint runs:

```powershell
python manage.py collectstatic --noinput
```

Nginx serves `/static/` from the collected static volume and proxies dynamic requests to Django.
Nginx does not serve private archived PDF/XLSX files. Archived documents continue to download only
through authorized Django views.

## Deploy Commands

Build and start the deployment stack:

```powershell
docker compose -f docker-compose.deploy.yml up -d --build
```

The deploy compose publishes MinIO ports for local Phase 18 verification:

```powershell
docker compose -f docker-compose.deploy.yml up -d --build
```

Then open `http://localhost:9001`, create the private `ecologist-documents` bucket, and only then
set `USE_S3_STORAGE=True` for manual archive storage checks. For real production, close MinIO
ports or move them to a private local override; archived documents must still download through
authorized Django views, not public MinIO URLs.

Run migrations explicitly:

```powershell
docker compose -f docker-compose.deploy.yml exec web python manage.py migrate
```

The app healthcheck endpoint is:

```text
/healthz/
```

It returns only `ok` and does not expose database, MinIO or secret state.

## Manual PostgreSQL Backup And Restore

Backup:

```powershell
docker compose -f docker-compose.deploy.yml exec db pg_dump -U ecologist -d ecologist -Fc -f /tmp/ecologist.dump
docker compose -f docker-compose.deploy.yml cp db:/tmp/ecologist.dump .\ecologist.dump
```

Restore:

```powershell
docker compose -f docker-compose.deploy.yml cp .\ecologist.dump db:/tmp/ecologist.dump
docker compose -f docker-compose.deploy.yml exec db pg_restore -U ecologist -d ecologist --clean --if-exists /tmp/ecologist.dump
```

Scheduled backups, TLS certificate automation, monitoring and full VPS/cloud hardening are outside
Phase 18.
