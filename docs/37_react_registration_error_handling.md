# Phase 37 - React Registration Error Handling

## Summary

Phase 37 fixes the React manager registration failure path. Duplicate username/email and other
validation failures now show user-facing Russian messages instead of leaving the submit button in a
loading state.

## Implemented

- `POST /api/v1/auth/register/` keeps using `ManagerRegistrationForm`, but validation errors are
  normalized as arrays of strings for stable React rendering.
- React `/register` supports field errors, nested error payloads, server/network fallback messages
  and timeout messages.
- React `/register` restores the Django-template phone normalization on blur and redirects to
  `/login` without showing a post-registration success banner.
- Registration requests time out instead of waiting indefinitely.
- Playwright auth smoke covers duplicate `manager_demo` / `manager@example.com` registration.

## Out Of Scope

- No database or migration changes.
- No changes to manager-only registration rules.
- No changes to JWT token obtain/refresh behavior.
- No changes to Django-template registration.

## Verification

- Backend tests cover duplicate username/email and invalid phone/password error payloads.
- Frontend smoke confirms duplicate registration warnings are visible and the submit button becomes
  enabled again.
