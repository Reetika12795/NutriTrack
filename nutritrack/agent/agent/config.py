"""Configuration for the NutriTrack health agent."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class AgentConfig(BaseSettings):
    """Agent configuration loaded from environment variables."""

    anthropic_api_key: str = ""
    model: str = "claude-sonnet-4-20250514"

    # NutriTrack service URLs (defaults for Docker Compose)
    airflow_url: str = "http://localhost:8080"
    fastapi_url: str = "http://localhost:8000"
    streamlit_url: str = "http://localhost:8501"
    superset_url: str = "http://localhost:8088"
    grafana_url: str = "http://localhost:3000"
    minio_url: str = "http://localhost:9001"
    mailhog_url: str = "http://localhost:8025"

    # Default credentials
    airflow_user: str = "admin"
    airflow_password: str = "admin"
    grafana_user: str = "admin"
    grafana_password: str = "admin"
    superset_user: str = "admin"
    superset_password: str = "admin"
    minio_user: str = "minioadmin"
    minio_password: str = "minioadmin123"

    # Agent settings
    screenshot_dir: str = "screenshots"
    headless: bool = True
    timeout_ms: int = 10000
    max_retries: int = 3

    model_config = {"env_prefix": "AGENT_"}
