FROM apache/superset:latest

USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3-pip && \
    pip install --no-cache-dir --target=/app/.venv/lib/python3.10/site-packages psycopg2-binary && \
    apt-get purge -y python3-pip && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*
USER superset
