# Technical Monitoring Newsletter - NutriTrack

**Project**: NutriTrack - Nutritional Tracking Platform
**Period**: Week of March 10, 2026
**Author**: Data Engineering Team
**Frequency**: Weekly (minimum 1 hour / week)

---

## 1. Monitoring Topic: Apache Superset 6.0 - BI and Analytical Visualization

### 1.1 Context and Rationale

Apache Superset was selected as the BI tool for the NutriTrack project (evaluation E5, competency C14) to provide business teams (nutritionists, analysts) with autonomous access to data warehouse content. This bulletin covers the major changes in version 6.0, which is deployed in the project.

### 1.2 Superset 6.0.1 New Features

| Feature | NutriTrack Impact | Status |
|---|---|---|
| **Renamed visualization types** (e.g. `dist_bar` -> `echarts_bar`, `pie` -> `echarts_pie`) | Mandatory migration of existing dashboards | Integrated |
| **Native cross-dashboard filters** (`DASHBOARD_CROSS_FILTERS`) | Enables interactive filtering between Nutri-Score charts and nutritional trend visualizations | Enabled |
| **Template processing** (`ENABLE_TEMPLATE_PROCESSING`) | Dynamic SQL queries with Jinja variables in datasets | Enabled |
| **Integrated Redis cache** | Improved dashboard response time (TTL 300s configured) | Deployed |

### 1.3 Technical Decision Made

Legacy visualization type names (`dist_bar`, `pie`, `line`) are no longer recognized in Superset 6.x. The `superset/bootstrap_dashboards.py` script was updated to use exclusively ECharts types (`echarts_bar`, `echarts_pie`, `echarts_timeseries_line`). This migration was validated across all 4 NutriTrack dashboards.

### 1.4 Sources Consulted

| Source | Reliability | URL/Reference |
|---|---|---|
| Apache Superset Release Notes | Official (ASF) | github.com/apache/superset/releases |
| Superset Documentation | Official | superset.apache.org/docs |
| Superset GitHub Issues | Community (verified) | Tickets #28xxx series on ECharts migration |

---

## 2. Regulatory Monitoring: GDPR and Nutritional Data

### 2.1 Key Concern

The European Data Protection Board (EDPB) published updated guidelines on the processing of health and wellness data in mobile applications (Guidelines 01/2026). Dietary tracking data (meals, caloric intake) is classified as **sensitive data** when it can be used to infer an individual's health status.

### 2.2 Impact on NutriTrack

| Existing Measure | Compliance |
|---|---|
| SHA256 pseudonymization of user identifiers in the data warehouse | Compliant |
| GDPR registry (`rgpd_data_registry`) with legal bases and retention periods | Compliant |
| Automatic deletion of meal data older than 2 years (`rgpd_cleanup_expired_data()`) | Compliant |
| Explicit consent at registration (mandatory `consent_date` field) | Compliant |

### 2.3 Recommended Action

No immediate corrective action required. Continue monitoring EDPB and CNIL publications to anticipate potential changes to consent requirements.

---

## 3. Tool Monitoring: Apache Airflow 2.8 - ETL Orchestration

### 3.1 Relevant Updates

- **Object Storage backend**: Airflow 2.8 introduces native support for object storage backends (S3, GCS, Azure Blob). NutriTrack already uses MinIO as its data lake; this feature could simplify connections in future DAGs.
- **Improved listener hooks**: The `on_task_instance_failed` and `on_task_instance_success` hooks enable custom callbacks, useful for enriching the alerting system (C16).

### 3.2 Sources Consulted

| Source | Reliability |
|---|---|
| Apache Airflow Changelog (apache/airflow) | Official (ASF) |
| Astronomer Blog | Industry (verified) |

---

## 4. Summary and Action Items

| Priority | Action | Deadline | Owner |
|---|---|---|---|
| High | Validate Superset dashboard compatibility after 6.0.1 upgrade | Done | Data Engineer |
| Medium | Monitor EDPB/CNIL publications on wellness data | Ongoing | DPO / Data Engineer |
| Low | Evaluate Airflow 2.8 Object Storage backend to simplify MinIO DAGs | Next sprint | Data Engineer |

---

*This bulletin is produced as part of technical and regulatory monitoring (competency C4) for the NutriTrack project. Frequency: weekly, minimum duration: 1 hour per week. Sources are evaluated according to the following reliability criteria: official (publisher/organization), verified community (peer-reviewed, >1000 contributors), industry (verified through experience).*
