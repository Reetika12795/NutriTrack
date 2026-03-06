import os

# Superset metadata database (stores dashboards, users, settings)
SQLALCHEMY_DATABASE_URI = os.environ.get(
    "SUPERSET_SQLALCHEMY_DATABASE_URI",
    "postgresql+psycopg2://superset:superset@postgres:5432/superset",
)

# Required since Superset 2.1.0
SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "nutritrack-superset-change-in-production")

# Server config
SUPERSET_WEBSERVER_PORT = 8088

# Disable examples to keep it clean
LOAD_EXAMPLES = False

# Enable CSRF protection
WTF_CSRF_ENABLED = True
WTF_CSRF_EXEMPT_LIST = []
WTF_CSRF_TIME_LIMIT = 60 * 60 * 24 * 365

# Feature flags
FEATURE_FLAGS = {
    "DASHBOARD_NATIVE_FILTERS": True,
    "DASHBOARD_CROSS_FILTERS": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
}

# Row limit for queries
ROW_LIMIT = 50000
SQL_MAX_ROW = 100000

# Cache config (uses Redis from the stack)
CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_KEY_PREFIX": "superset_",
    "CACHE_REDIS_URL": os.environ.get("REDIS_URL", "redis://redis:6379/2"),
}
