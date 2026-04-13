"""Shared test fixtures for the NutriTrack test suite."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Ensure the nutritrack package root is importable
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def pytest_configure(config):
    """Patch pydantic-settings to ignore .env files during testing.

    The .env file contains variables (POSTGRES_USER, AIRFLOW__CORE__EXECUTOR,
    etc.) that are not declared in api.config.Settings.  Since pydantic v2
    defaults to extra='forbid', importing api.config at collection time would
    raise a ValidationError.  We avoid this by ensuring the env file is not
    loaded.
    """
    # Point away from the real .env so Settings() won't pick up stray vars.
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
    os.environ.setdefault("DATABASE_URL_SYNC", "postgresql+psycopg2://test:test@localhost:5432/test")

    # Patch BaseSettings to skip env file reading
    try:
        from pydantic_settings import BaseSettings

        original_init = BaseSettings.__init__

        def patched_init(self, **kwargs):
            kwargs.setdefault("_env_file", None)
            original_init(self, **kwargs)

        BaseSettings.__init__ = patched_init
    except ImportError:
        pass


@pytest.fixture
def sample_product_data():
    """Return valid product data for schema tests."""
    return {
        "product_id": 1,
        "barcode": "3017620422003",
        "product_name": "Nutella",
        "energy_kcal": 539.0,
        "fat_g": 30.9,
        "proteins_g": 6.3,
        "nutriscore_grade": "E",
        "nova_group": 4,
    }


@pytest.fixture
def sample_user_data():
    """Return valid user registration data."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "securepassword123",
        "consent_data_processing": True,
    }
