# Phase 20 JWT API Authentication

Phase 20 adds JWT authentication for external REST API clients. It does not replace Django
sessions used by the Russian HTML web interface.

## Scope

- Web UI login, logout, registration and profile pages keep using Django sessions.
- API business endpoints remain read-only.
- JWT is available only for authenticated API access with `Authorization: Bearer <access_token>`.
- CORS, OAuth, token blacklist, refresh rotation and token logout are not implemented in this
  phase. Phase 21 adds Swagger/OpenAPI documentation for the existing JWT-protected API.

## Token Endpoints

All endpoints are under `/api/v1/auth/`.

### Obtain Token

```http
POST /api/v1/auth/token/
Content-Type: application/json

{
  "username": "manager_demo",
  "password": "Manager12345!"
}
```

Response:

```json
{
  "refresh": "...",
  "access": "..."
}
```

### Refresh Access Token

```http
POST /api/v1/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "..."
}
```

### Verify Token

```http
POST /api/v1/auth/token/verify/
Content-Type: application/json

{
  "token": "..."
}
```

### Current User

```http
GET /api/v1/auth/me/
Authorization: Bearer <access_token>
```

Response:

```json
{
  "id": 1,
  "username": "manager_demo",
  "full_name": "",
  "role": "manager"
}
```

The response intentionally does not expose password hash, email, phone, middle name, staff flags,
superuser flags or secrets.

## Calling Read-Only API

```http
GET /api/v1/orders/
Authorization: Bearer <access_token>
```

Manager and admin access rules are the same as with session-authenticated API calls:

- managers see only their own orders, trips and analytics;
- admins and superusers see company-level data;
- business endpoints do not accept writes and return `405` for `POST`, `PUT`, `PATCH` and
  `DELETE`.

## Swagger Authorization

Phase 21 adds Swagger UI at `/api/docs/`.

1. Call `POST /api/v1/auth/token/` with a valid username and password.
2. Copy the `access` value from the response.
3. Open `/api/docs/`, click `Authorize`, and enter `Bearer <access_token>`.
4. Use the documented `GET` endpoints. Business `POST`, `PUT`, `PATCH` and `DELETE` methods remain
   unavailable and return `405`.

## Token Settings

- Access token lifetime: 15 minutes.
- Refresh token lifetime: 1 day.
- Header type: `Bearer`.
- No blacklist app.
- No refresh token rotation.
- No token logout endpoint.

## Security Notes

- Use JWT only over HTTPS in production.
- Store refresh tokens carefully on the client side.
- JWT does not replace Django password hashing.
- JWT does not replace Django sessions for the HTML interface.
- API responses continue to avoid raw provider payloads, MinIO/S3 paths, full
  `calculation_details_json`, geometry and internal debug fields.
