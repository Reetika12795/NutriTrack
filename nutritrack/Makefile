# NutriTrack - Development Makefile
# Quick commands for common operations

.PHONY: help up down build logs extract clean import api app setup-lake backup

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# === Docker Compose ===

up: ## Start all services
	docker compose up -d

down: ## Stop all services
	docker compose down

build: ## Build and start services
	docker compose up -d --build

logs: ## View all logs
	docker compose logs -f

logs-api: ## View API logs
	docker compose logs -f fastapi

logs-airflow: ## View Airflow logs
	docker compose logs -f airflow-webserver airflow-scheduler

# === Data Pipeline ===

extract-api: ## Run API extraction script
	python scripts/extract_off_api.py --mode category --max-pages 3

extract-parquet: ## Run Parquet extraction with DuckDB
	python scripts/extract_off_parquet.py --countries France --limit 50000

extract-scraping: ## Run web scraping for guidelines
	python scripts/extract_scraping.py --sources all

extract-db: ## Run database extraction queries
	python scripts/extract_from_db.py --queries all

extract-duckdb: ## Run DuckDB big data analytics
	python scripts/extract_duckdb.py --queries all

extract-all: extract-api extract-parquet extract-scraping ## Run all extractions

clean-data: ## Run aggregation and cleaning pipeline
	python scripts/aggregate_clean.py --sources all

import-db: ## Import cleaned data into PostgreSQL
	python scripts/import_to_db.py

pipeline: extract-all clean-data import-db ## Run full extraction -> clean -> import pipeline

# === Data Lake ===

setup-lake: ## Setup MinIO data lake (buckets, policies, catalog)
	python scripts/setup_minio.py --all

lake-status: ## Check data lake storage status
	python scripts/setup_minio.py --check-status

# === Database ===

backup: ## Run database backup
	python scripts/backup_database.py --type full --upload

backup-dw: ## Backup data warehouse only
	python scripts/backup_database.py --type dw_only --upload

# === Development ===

api: ## Run FastAPI locally (development)
	cd api && uvicorn api.main:app --reload --port 8000

app: ## Run Streamlit locally (development)
	streamlit run app/streamlit_app.py

install: ## Install Python dependencies
	pip install -r requirements.txt
	pip install -r api/requirements.txt
	pip install -r app/requirements.txt

# === Testing ===

test-api: ## Test API endpoints with curl
	@echo "=== Health Check ==="
	curl -s http://localhost:8000/ | python -m json.tool
	@echo "\n=== Register User ==="
	curl -s -X POST http://localhost:8000/api/v1/auth/register \
		-H "Content-Type: application/json" \
		-d '{"email":"test@test.com","username":"testuser","password":"test123","consent_data_processing":true}' | python -m json.tool
	@echo "\n=== Login ==="
	curl -s -X POST http://localhost:8000/api/v1/auth/login \
		-H "Content-Type: application/json" \
		-d '{"username":"testuser","password":"test123"}' | python -m json.tool
