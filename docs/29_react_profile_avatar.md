# Phase 29 - React Profile Avatar

## Summary

Phase 29 adds the React profile page and JWT-protected avatar handling for the current user.

- `/profile` is available inside the React SPA for authenticated users.
- Profile data is loaded and updated through `/api/v1/profile/`.
- Avatar upload, download and delete use `/api/v1/profile/avatar/`.
- Existing Django profile pages and session-based avatar views remain available.

## Backend

The `accounts.User.avatar` field and private avatar storage already existed before this phase, so
no new model migration is required.

The API exposes only safe current-user profile fields:

- `id`
- `username`
- `first_name`
- `last_name`
- `middle_name`
- `email`
- `phone`
- `role`
- `avatar_exists`

`PATCH /api/v1/profile/` updates only editable personal fields. It ignores protected identity and
permission fields such as `username`, `role`, `is_staff`, `is_superuser` and password data.

## Avatar Rules

Avatar files are validated without Pillow:

- allowed formats: JPG, JPEG, PNG, WEBP;
- maximum size: 5 MB;
- extension, content type and file header are checked;
- raw storage paths and S3/MinIO URLs are not exposed in JSON responses.

Local storage uses `protected_media/profile_avatars`. When S3 storage is enabled, avatars use the
same private S3-compatible storage strategy as protected project files.

## Frontend

The React page includes:

- avatar card with default local SVG fallback;
- upload/change/delete avatar actions;
- personal data card with read and edit modes;
- Russian loading, success and error states;
- role shown as a green badge.

The uploaded avatar is fetched as a protected blob through RTK Query and displayed with a temporary
object URL that is revoked when the component changes or unmounts.

## Scope Preserved

- Django templates are not removed.
- Login/logout behavior is unchanged.
- Business calculations, route providers, reports and archive behavior are unchanged.
- Admin SPA and production React/Nginx deployment remain deferred.
