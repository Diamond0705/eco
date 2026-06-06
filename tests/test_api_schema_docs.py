import json

BUSINESS_PATHS = [
    "/api/v1/locations/",
    "/api/v1/transports/",
    "/api/v1/orders/",
    "/api/v1/orders/{id}/",
    "/api/v1/trips/",
    "/api/v1/analytics/summary/",
]

EXPECTED_PATHS = BUSINESS_PATHS + [
    "/api/v1/auth/token/",
    "/api/v1/auth/token/refresh/",
    "/api/v1/auth/token/verify/",
    "/api/v1/auth/me/",
]

FORBIDDEN_SCHEMA_FIELDS = [
    "password_hash",
    "calculation_details_json",
    "route_facts_json",
    "geometry_json",
    "AWS_SECRET_ACCESS_KEY",
    "GRAPHHOPPER_API_KEY",
]


def openapi_schema(client):
    response = client.get("/api/schema/", HTTP_ACCEPT="application/json")
    assert response.status_code == 200
    return response.json()


def test_openapi_schema_endpoint_returns_schema(client):
    schema = openapi_schema(client)

    assert schema["info"]["title"] == "EcoLogist API"
    assert schema["info"]["version"] == "1.0.0"


def test_swagger_and_redoc_pages_return_200(client):
    docs_response = client.get("/api/docs/")
    redoc_response = client.get("/api/redoc/")

    assert docs_response.status_code == 200
    assert redoc_response.status_code == 200


def test_openapi_schema_contains_existing_api_paths(client):
    schema = openapi_schema(client)

    for path in EXPECTED_PATHS:
        assert path in schema["paths"]


def test_openapi_schema_documents_business_api_as_read_only(client):
    schema = openapi_schema(client)

    for path in BUSINESS_PATHS:
        assert set(schema["paths"][path]) == {"get"}


def test_openapi_schema_uses_bearer_auth_for_api_paths(client):
    schema = openapi_schema(client)
    security_schemes = schema["components"]["securitySchemes"]

    assert "jwtAuth" in security_schemes
    assert security_schemes["jwtAuth"]["type"] == "http"
    assert security_schemes["jwtAuth"]["scheme"] == "bearer"


def test_openapi_schema_does_not_expose_internal_fields(client):
    schema_text = json.dumps(openapi_schema(client))

    for field in FORBIDDEN_SCHEMA_FIELDS:
        assert field not in schema_text
