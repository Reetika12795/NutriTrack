"""
NutriTrack REST API - Main application
Covers: C12 - REST API with OpenAPI documentation, JWT auth, role-based access
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.routers import analytics, auth, meals, nutritionist, products

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "NutriTrack API - A fitness nutrition tracker powered by Open Food Facts.\n\n"
        "## Authentication\n"
        "All endpoints require JWT authentication. Obtain a token via `/api/v1/auth/login`.\n\n"
        "## Roles\n"
        "- **user**: Search products, log meals, view personal nutrition data\n"
        "- **nutritionist**: All user permissions + access to aggregated analytics\n"
        "- **admin**: Full access including raw data and management endpoints\n"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(meals.router)
app.include_router(analytics.router)
app.include_router(nutritionist.router)


@app.get("/", tags=["Health"])
async def root():
    """API health check endpoint."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy",
    }


@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "api_version": settings.APP_VERSION,
        "docs": "/docs",
    }
