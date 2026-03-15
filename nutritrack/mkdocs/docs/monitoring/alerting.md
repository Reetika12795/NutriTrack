# Alerting System

## Overview (C16)

Multi-layered alerting system that logs events to a database, sends email notifications, and displays metrics on Grafana dashboards.

## Alert Architecture

```mermaid
graph TD
    subgraph Airflow["Airflow DAGs"]
        TF["Task Failure"]
        TR["Task Retry"]
        SM["SLA Miss"]
        TS["Task Success"]
    end

    subgraph Callbacks["alerting.py Callbacks"]
        C1["on_failure_callback<br/>→ CRITICAL"]
        C2["on_retry_callback<br/>→ WARNING"]
        C3["sla_miss_callback<br/>→ WARNING"]
        C4["on_success_callback<br/>→ INFO"]
    end

    subgraph Actions["Alert Actions"]
        DB[("etl_activity_log<br/>PostgreSQL")]
        EM["Email via MailHog<br/>:8025"]
        SD["StatsD Metrics<br/>→ Prometheus"]
    end

    subgraph Dashboards["Visualization"]
        GF["Grafana SLA Dashboard"]
        AF["Airflow UI"]
    end

    TF --> C1
    TR --> C2
    SM --> C3
    TS --> C4

    C1 --> DB & EM
    C2 --> DB
    C3 --> DB & EM
    C4 --> DB

    C1 & C2 & C3 & C4 --> SD
    SD --> GF
    DB --> GF
    DB --> AF

    style Airflow fill:#f3e5f5,stroke:#6a1b9a
    style Callbacks fill:#fff3e0,stroke:#e65100
    style Actions fill:#e3f2fd,stroke:#1565c0
    style Dashboards fill:#e8f5e9,stroke:#2e7d32
```

## Alert Categories

| Category | Severity | Trigger | Response |
|----------|----------|---------|----------|
| **CRITICAL** | P1 | Task failure | Immediate investigation, email alert |
| **WARNING** | P2 | Task retry, SLA miss | Investigate within 4 hours |
| **INFO** | P4 | Task success, routine operations | No action needed |

## Activity Log Schema

```sql
CREATE TABLE app.etl_activity_log (
    log_id          SERIAL PRIMARY KEY,
    dag_id          VARCHAR(100),
    task_id         VARCHAR(100),
    execution_date  TIMESTAMP,
    event_type      VARCHAR(50),    -- task_failure, task_success, sla_miss, ...
    alert_category  VARCHAR(20),    -- CRITICAL, WARNING, INFO
    message         TEXT,
    details         JSONB,          -- structured context (exception, duration, etc.)
    created_at      TIMESTAMP DEFAULT NOW()
);
```

## SMTP Configuration

MailHog provides a test SMTP server for capturing email alerts during development and demos:

```yaml
# docker-compose.yml
mailhog:
  image: mailhog/mailhog:latest
  ports:
    - "1025:1025"   # SMTP server
    - "8025:8025"   # Web UI to view emails

# Airflow SMTP settings
AIRFLOW__SMTP__SMTP_HOST: mailhog
AIRFLOW__SMTP__SMTP_PORT: "1025"
AIRFLOW__SMTP__SMTP_MAIL_FROM: "airflow@nutritrack.local"
```

**Web UI**: http://localhost:8025 — view all captured alert emails.

## Maintenance Priority Matrix (ITIL)

```mermaid
graph TD
    subgraph P1["P1 — Critical<br/>Response: < 1 hour"]
        P1A["Database down"]
        P1B["Data loss detected"]
        P1C["Security breach"]
    end

    subgraph P2["P2 — High<br/>Response: < 4 hours"]
        P2A["ETL pipeline failure"]
        P2B["SLA breach"]
        P2C["Storage > 90%"]
    end

    subgraph P3["P3 — Medium<br/>Response: < 24 hours"]
        P3A["Performance degradation"]
        P3B["Non-critical DAG failure"]
        P3C["Data quality warning"]
    end

    subgraph P4["P4 — Low<br/>Response: Next sprint"]
        P4A["Documentation update"]
        P4B["Optimization opportunity"]
        P4C["Minor UI issue"]
    end

    style P1 fill:#f44336,color:#fff
    style P2 fill:#ff9800,color:#fff
    style P3 fill:#ffc107
    style P4 fill:#4caf50,color:#fff
```

## Escalation Procedure

| Level | Who | When |
|-------|-----|------|
| **L1** | Data Engineer on-call | First response, investigate |
| **L2** | Senior Data Engineer | L1 unable to resolve in SLA |
| **L3** | Platform Architect | System-wide or architectural issue |
