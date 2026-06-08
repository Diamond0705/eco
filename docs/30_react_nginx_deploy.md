# Phase 30 - React Nginx Production Deploy

## Summary

Phase 30 updates the production-like Docker/Nginx path so Nginx serves the built React SPA and
proxies backend routes to Django/Waitress.

The Django backend remains the source of truth. Django templates and Django Admin remain in the
project, but the production root route now serves the React SPA.

## Build Strategy

The Django `web` image remains Python + Waitress.

The Nginx image is built from `docker/nginx/Dockerfile`:

1. `node:22-alpine` installs frontend dependencies with `npm ci`.
2. The React app is built with `npm run build`.
3. `frontend/dist` is copied into `nginx:1.27-alpine` at `/usr/share/nginx/html`.

`frontend/dist` is not committed. `.dockerignore` excludes local frontend build/cache folders and
`node_modules` from the Docker build context.

## Routing

Nginx serves:

- `/`
- `/login`
- `/register`
- `/dashboard`
- `/orders`
- `/orders/create`
- `/orders/:id`
- `/orders/:id/routes`
- `/trips`
- `/trips/:id`
- `/analytics`
- `/reports/emissions`
- `/archive`
- `/profile`
- `/admin/dashboard`
- `/admin/archive`
- `/admin/users`
- `/admin/transports`
- `/admin/locations`
- `/admin/eco-standards`
- `/admin/calculation-settings`
- `/admin/profile`

SPA fallback uses:

```nginx
try_files $uri $uri/ /index.html;
```

Nginx proxies these backend routes to Django/Waitress:

- `/api/`
- `/admin/`
- `/healthz/`
- `/accounts/`
- selected legacy protected download/action routes under `/reports/`, `/trips/` and `/profile/avatar/`.

`/api/unknown` is proxied to Django and must not return React `index.html`.
`/admin/` itself is still Django Admin; selected React admin routes such as `/admin/dashboard`
serve the SPA.

## Static And Protected Files

- React hashed assets are served by Nginx from `/usr/share/nginx/html/assets/`.
- Django collected static files are served from the `static_data` volume at `/static/`.
- Private archived documents and profile avatars are not exposed through Nginx aliases.
- Protected files continue to be downloaded through Django/API authorization.

## Deploy Commands

Build and start the production-like stack:

```powershell
docker compose -f docker-compose.deploy.yml up -d --build
```

Open:

```text
http://localhost/
```

Useful checks:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost/
Invoke-WebRequest -UseBasicParsing http://localhost/login
Invoke-WebRequest -UseBasicParsing http://localhost/register
Invoke-WebRequest -UseBasicParsing http://localhost/orders
Invoke-WebRequest -UseBasicParsing http://localhost/admin/dashboard
Invoke-WebRequest -UseBasicParsing http://localhost/api/v1/auth/me/
Invoke-WebRequest -UseBasicParsing http://localhost/healthz/
Invoke-WebRequest -UseBasicParsing http://localhost/admin/
```

Expected:

- `/`, `/login`, `/register`, `/orders` and `/admin/dashboard` return the React SPA.
- `/api/v1/auth/me/` reaches Django and returns `401` when anonymous.
- `/healthz/` returns `ok`.
- `/admin/` reaches Django Admin.

Stop the stack:

```powershell
docker compose -f docker-compose.deploy.yml down
```

## Local Development

Local development remains unchanged:

```powershell
.venv\Scripts\python.exe manage.py runserver
cd frontend
npm.cmd run dev
```

Vite continues to proxy `/api` and `/static` to `http://127.0.0.1:8000`, so CORS is not required
for the local React workflow.

## MinIO

The deploy compose keeps MinIO internal by default. For local MinIO console debugging, create a
separate local override that publishes `9000` and `9001`; do not expose those ports in production.

## Out Of Scope

- Real domain and TLS certificate automation.
- Celery, Redis and WebSocket background workflows.
- Changes to calculations, routing providers, reports, archive or profile avatar business logic.
