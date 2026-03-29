# NutriTrack Platform Health Agent

AI-powered UI health monitor that navigates NutriTrack service UIs, takes screenshots, and uses Claude's vision to analyze platform health.

## How It Works

```
┌─────────────┐     ┌──────────┐     ┌───────────┐     ┌──────────┐
│  Navigate UI │ ──→ │Screenshot│ ──→ │Claude API │ ──→ │  Report  │
│ (Playwright) │     │ (PNG)    │     │ (Vision)  │     │ (JSON)   │
└─────────────┘     └──────────┘     └───────────┘     └──────────┘
```

The agent loop for each service:
1. **Probe** — check if the service URL is reachable
2. **Navigate** — load the UI in a headless browser
3. **Login** — authenticate if required (Airflow, Grafana, Superset, MinIO)
4. **Screenshot** — capture the current state
5. **Analyze** — send screenshot to Claude for health assessment
6. **Report** — aggregate all results into a JSON report

## Quick Start

```bash
cd nutritrack/agent

# Install dependencies
pip install -e .
playwright install chromium

# Basic check (no AI — just reachability + screenshots)
nutritrack-agent check

# Full AI-powered analysis
AGENT_ANTHROPIC_API_KEY=sk-ant-... nutritrack-agent check

# With visible browser
nutritrack-agent check --visible
```

## Services Monitored

| Service | URL | Auth | What's Checked |
|---------|-----|------|----------------|
| Airflow | :8080 | admin/admin | DAG statuses, task failures |
| FastAPI | :8000 | — | Health endpoint, OpenAPI spec |
| Grafana | :3000 | admin/admin | SLA dashboard, alerts |
| Streamlit | :8501 | — | Page loads, data displayed |
| Superset | :8088 | admin/admin | Dashboard rendering |
| MinIO | :9001 | minioadmin/* | Bucket accessibility |
| MailHog | :8025 | — | SMTP test server |

## Output

The agent produces:
- **Screenshots** in `screenshots/` — PNG for each service
- **JSON report** in `screenshots/health_report_*.json` — structured health data
- **Terminal output** — Rich-formatted table with color-coded status

## Configuration

All settings via environment variables (prefix `AGENT_`):

```bash
AGENT_ANTHROPIC_API_KEY=sk-ant-...   # Required for AI analysis
AGENT_MODEL=claude-sonnet-4-20250514       # Claude model to use
AGENT_HEADLESS=true                  # Hide browser window
AGENT_TIMEOUT_MS=10000               # Page load timeout
AGENT_AIRFLOW_URL=http://localhost:8080
AGENT_GRAFANA_URL=http://localhost:3000
# ... etc for each service
```

## Architecture

```
agent/
├── agent/
│   ├── config.py       # Pydantic settings (env vars)
│   ├── browser.py      # Playwright browser controller
│   ├── vision.py       # Claude API for screenshot analysis
│   ├── core.py         # Agent loop: probe → navigate → screenshot → analyze → report
│   ├── cli.py          # CLI entry point
│   └── tasks/
│       └── health_check.py  # Deep health check (per-service navigation)
├── tests/
│   └── test_config.py
├── pyproject.toml
└── README.md
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All services healthy |
| 1 | Some services degraded |
| 2 | Critical — services down |
