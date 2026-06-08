# Phase 25 React SPA Scaffold

Phase 25 creates the initial React single-page application scaffold in `/frontend`. The React app
is a separate Vite frontend that talks to the existing Django REST API through `/api/v1/`.

This phase does not remove Django templates, change Django views, change backend business logic,
create migrations, add CORS, add WebSocket/Celery/Redis, or implement the full manager/admin SPA.

## Frontend Stack

- Vite.
- React with JavaScript.
- React Router.
- Redux Toolkit.
- RTK Query.
- React Redux.
- Plain project CSS.

React Leaflet is intentionally deferred to Phase 26, when route map pages are implemented.

## Created Structure

```text
frontend/
  package.json
  vite.config.js
  index.html
  src/
    main.jsx
    App.jsx
    app/store.js
    api/baseApi.js
    api/authApi.js
    features/auth/authSlice.js
    layouts/AppLayout.jsx
    pages/LoginPage.jsx
    pages/DashboardPage.jsx
    pages/NotFoundPage.jsx
    routes/ProtectedRoute.jsx
    routes/RoleRoute.jsx
    styles/app.css
```

## Development Flow

Run Django in one terminal:

```powershell
.venv\Scripts\python.exe manage.py runserver
```

Run Vite in another terminal:

```powershell
cd frontend
npm install
npm run dev
```

The Vite dev server serves the React SPA on its default port and proxies API requests to Django on
`http://127.0.0.1:8000`.

## Vite Proxy

`frontend/vite.config.js` proxies:

- `/api` to `http://127.0.0.1:8000`;
- `/static` to `http://127.0.0.1:8000` so the scaffold can reuse existing EcoLogist images.

This keeps Phase 25 same-origin from the browser's point of view and avoids adding CORS.

## Auth Strategy

- `POST /api/v1/auth/token/` is used for login.
- `GET /api/v1/auth/me/` loads the current user after login.
- Access token is stored only in Redux memory state.
- Refresh token is stored in `sessionStorage` for this scaffold phase.
- RTK Query attaches `Authorization: Bearer <access_token>`.
- On `401`, RTK Query tries `POST /api/v1/auth/token/refresh/` once, retries the original request,
  then clears auth state if refresh fails.
- Logout clears Redux auth state and `sessionStorage`.
- OAuth and HttpOnly refresh cookies are not implemented in Phase 25. HttpOnly refresh cookies can
  be considered as a later hardening phase.

## Routes

- `/login` - login page.
- `/` - redirects to `/dashboard` after authentication.
- `/dashboard` - protected placeholder dashboard.
- `*` - Russian not-found page.

`ProtectedRoute` checks auth state and loads the current user. `RoleRoute` checks the user role for
role-limited pages.

## UI Scope

- Russian UI only.
- EcoLogist green visual direction.
- Existing logo/static images reused through the Vite `/static` proxy.
- Layout includes a sidebar, topbar, logout action and placeholder navigation.
- Full manager pages are deferred to Phase 26.
- Admin SPA is deferred to Phase 27.

## Checks

Phase 25 should pass:

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.venv\Scripts\python.exe -m pytest --basetemp=.tmp\pytest
.venv\Scripts\python.exe -m ruff check .
cd frontend
npm install
npm run build
```
