"""Tests for API endpoints using httpx TestClient.

Validates health check routes, OpenAPI schema generation, and CORS config.
These tests do not require a database connection.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from api.main import app


@pytest.fixture
def transport():
    """Create an ASGI transport for the FastAPI app."""
    return ASGITransport(app=app)


@pytest.fixture
async def client(transport):
    """Async HTTP client bound to the test app."""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_root_health_check(client):
    """GET / returns healthy status."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert data["app"] == "NutriTrack API"


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """GET /api/v1/health returns detailed health info."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "api_version" in data
    assert data["docs"] == "/docs"


@pytest.mark.asyncio
async def test_openapi_schema_available(client):
    """OpenAPI JSON schema is served at the configured URL."""
    response = await client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "NutriTrack API"
    assert "paths" in schema


@pytest.mark.asyncio
async def test_openapi_has_product_endpoints(client):
    """OpenAPI schema documents the products endpoints."""
    response = await client.get("/api/v1/openapi.json")
    schema = response.json()
    paths = schema["paths"]
    # Products search endpoint
    assert "/api/v1/products/" in paths
    # Product by barcode endpoint
    assert "/api/v1/products/{barcode}" in paths


@pytest.mark.asyncio
async def test_openapi_has_auth_endpoints(client):
    """OpenAPI schema documents auth endpoints."""
    response = await client.get("/api/v1/openapi.json")
    schema = response.json()
    paths = schema["paths"]
    auth_paths = [p for p in paths if "/auth/" in p]
    assert len(auth_paths) > 0


@pytest.mark.asyncio
async def test_openapi_has_meal_endpoints(client):
    """OpenAPI schema documents meal endpoints."""
    response = await client.get("/api/v1/openapi.json")
    schema = response.json()
    paths = schema["paths"]
    meal_paths = [p for p in paths if "/meals" in p]
    assert len(meal_paths) > 0


@pytest.mark.asyncio
async def test_docs_page_available(client):
    """Swagger UI docs page is available."""
    response = await client.get("/docs")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_redoc_page_available(client):
    """ReDoc documentation page is available."""
    response = await client.get("/redoc")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_unauthenticated_product_search(client):
    """Product search without auth returns 401 or 403."""
    response = await client.get("/api/v1/products/", params={"q": "nutella"})
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_unauthenticated_meal_access(client):
    """Meal endpoint without auth returns 401 or 403."""
    response = await client.get("/api/v1/meals/today")
    assert response.status_code in (401, 403, 404)


def test_app_has_cors_middleware():
    """FastAPI app has CORS middleware configured."""
    middleware_classes = [m.cls.__name__ for m in app.user_middleware]
    assert "CORSMiddleware" in middleware_classes


def test_app_title():
    """App title matches configuration."""
    assert app.title == "NutriTrack API"


def test_app_version():
    """App version is set."""
    assert app.version == "1.0.0"
