"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://nutritrack:nutritrack@localhost:5432/nutritrack"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://nutritrack:nutritrack@localhost:5432/nutritrack"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/1"

    # JWT
    JWT_SECRET_KEY: str = "nutritrack-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"

    # App
    APP_NAME: str = "NutriTrack API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
