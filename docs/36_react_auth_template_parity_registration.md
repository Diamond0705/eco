# Phase 36 - React Auth Template Parity And Registration

## Summary

Phase 36 aligns the unauthenticated React screens with the existing Django login and registration
templates and adds manager registration to the React SPA.

The backend remains Django + DRF + SimpleJWT. Django templates stay available as legacy/fallback
views, and Django Admin remains available at `/admin/`.

## Implemented

- React `/login` uses the Django-template visual language: white topbar, EcoLogist logo,
  `login-background.png`, `login-card-background.png`, green buttons and Russian labels.
- React `/register` creates manager accounts through the API and mirrors the Django registration
  form fields, placeholders and helper text.
- `POST /api/v1/auth/register/` is public and uses `ManagerRegistrationForm`, so username/email
  uniqueness, phone normalization, password validation and manager role assignment stay shared
  with the template flow.
- Successful React registration redirects to `/login` with the message
  `Регистрация завершена. Теперь войдите в систему.`

## Out Of Scope

- No model changes or migrations.
- No changes to JWT token obtain/refresh behavior.
- No auto-login after registration.
- No admin-user registration flow in React.
- No changes to calculations, route providers, reports, archive, Django templates or Django Admin.

## Verification

- Backend API tests cover successful manager registration, safe response shape, duplicate
  username/email errors, invalid phone/password errors and role assignment.
- React E2E smoke covers `/login` and `/register` rendering with Russian text and no mojibake.
- Production-like Nginx routing documentation includes `/register` as an SPA route.
