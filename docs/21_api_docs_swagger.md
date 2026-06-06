# Phase 21 API Docs And Swagger

Phase 21 adds OpenAPI documentation for the existing read-only EcoLogist REST API. It does not add
write endpoints and does not change authentication, routing providers, calculation formulas,
reports, archives or HTML views.

## URLs

- `GET /api/schema/` - OpenAPI schema.
- `GET /api/docs/` - Swagger UI.
- `GET /api/redoc/` - ReDoc view.

The documented business API remains under `/api/v1/`:

- `GET /api/v1/locations/`
- `GET /api/v1/transports/`
- `GET /api/v1/orders/`
- `GET /api/v1/orders/<id>/`
- `GET /api/v1/trips/`
- `GET /api/v1/analytics/summary/`

JWT endpoints are documented under `/api/v1/auth/`.

## Swagger With JWT

1. Open `/api/docs/`.
2. Use `POST /api/v1/auth/token/` with a valid username and password.
3. Copy the returned `access` token.
4. Click `Authorize`.
5. Enter `Bearer <access_token>`.
6. Run the documented `GET` endpoints.

Business `POST`, `PUT`, `PATCH` and `DELETE` endpoints are not implemented and return
`405 Method Not Allowed`.

## Postman Import

Import the schema URL into Postman:

- local development: `http://127.0.0.1:8000/api/schema/`
- deployment: `https://<host>/api/schema/`

After import, obtain an access token from `POST /api/v1/auth/token/` and set collection
authorization to Bearer Token. Use the `access` token value without changing API field names.

## Safety Boundaries

The schema documents safe serializer fields only. API responses must not expose password hashes,
secrets, API keys, MinIO/S3 internal paths, raw GraphHopper responses, route geometry,
`route_facts_json` or full `calculation_details_json`.

OpenAPI documentation is for inspection and integration testing only. CORS, OAuth, write API,
pagination, throttling and public versioning policy remain future scope decisions.
