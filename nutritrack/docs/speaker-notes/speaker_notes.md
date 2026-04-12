# NutriTrack Defense - Speaker Notes

> What to say on each slide. Read this before the demo. Keep it natural - these are talking points, not a script to read word-for-word.

---

## SLIDE 1: Title

**Say (10 seconds):**
"Good morning, my name is Reetika Gautam. Today I am presenting NutriTrack, a nutritional data engineering platform, for my RNCP level 7 certification in Massive Data Infrastructures."

> Tip: Smile, pause, make eye contact. First impression matters.

---

## SLIDE 2: Defense Agenda - 90 Minutes

**Say (30 seconds):**
"Here is the plan for the next 90 minutes. I will spend the first 60 minutes presenting evaluations E1 through E5 - that covers the project from need analysis all the way through the data warehouse. I will include live demos throughout. Then 10 minutes for E6, the warehouse maintenance Q&A. Then 10 minutes for E7, the data lake. And we finish with 10 minutes of jury questions."

"The report has been handed to you, the code is on GitHub, and I will do live demos at each stage."

---

## SLIDE 3: Meet the Client - Ms. Sophie Yang

**Say (60 seconds):**
"Let me introduce the client who drives this entire project: Sophie Yang, a dietician in Paris who sees over 40 patients per week."

"Sophie has five daily pain points:" *(point to each one)*

1. "She manually searches Open Food Facts to look up products - this takes hours"
2. "She calculates macronutrients in spreadsheets - error-prone and slow"
3. "She cannot track patient progress over time"
4. "Her data is scattered across five or more tools and sources"
5. "She handles sensitive health data with zero RGPD compliance"

"Her exact words: *I spend hours looking up products. I need a platform where my patients log meals and I see the analytics.*"

"This is competency C1 - analyzing a data project need expression. Sophie's pain points drive every technical choice in this project."

> Tip: This slide sets up the ENTIRE narrative. Every feature you demo later maps back to a Sophie pain point.

---

## SLIDE 4: Interview Grids (C1) - MOVED HERE

**Say (30 seconds):**
"So starting from Sophie's pain points, the first thing I did was formalize the need analysis. I created two interview grids: one for data producers - the people who create and manage the data - and one for data consumers - Sophie and her team who will use the platform."

"The producer grid asks about business activities, data types, volumes, quality controls, and access constraints. The consumer grid asks about analysis objectives, granularity, delivery format, RGPD constraints, and accessibility needs."

"These grids are the foundation for every technical decision that follows."

> Tip: This now flows naturally - "Sophie has problems" → "I analyzed those problems formally" → "Here is what I built."

---

## SLIDE 5: SMART Objectives (C1) - MOVED HERE

**Say (30 seconds):**
"From the interviews, I defined SMART objectives."

"Specific: centralize data from 5+ sources. Measurable: 777,000+ products with sub-5-second queries. Achievable: all open-source, Docker-based. Relevant: directly addresses Sophie's fragmented nutrition data problem. Time-bound: 12-week timeline."

"The pre-project includes technical recommendations, RGPD action plan, accessibility planning, and RICE prioritization for feature ordering."

---

## SLIDE 6: NutriTrack - Built for Sophie

**Say (45 seconds):**
"So now that you understand the need and the objectives, here is what we built, mapped directly to Sophie's needs."

*(Point to each pair)*
- "She searches products manually? We built 5 automated extractors and a unified product search."
- "She cannot track patient meals? We built a meal logger with daily dashboards and weekly trends."
- "She worries about compliance? We implemented full RGPD: consent tracking, data registry, automatic cleanup, and pseudonymization."

"In total: 777,000+ products, 14 Docker services, 7 Airflow DAGs, 4 user roles, and the entire platform deploys with a single command."

---

## SLIDE 7: Open Food Facts - Primary Data Source

**Say (45 seconds):**
"Our primary data source is Open Food Facts, a French non-profit founded in 2012. It is like Wikipedia for food products - community-driven, with over 3 million products and 30,000 contributors."

"What makes it valuable for us: it provides Nutri-Score from A to E for nutrition quality, NOVA groups 1 to 4 for processing level, Eco-Score for environmental impact, full ingredient lists, allergen declarations, and 31 nutritional fields per product."

"It is open-source under ODbL license, used by well-known apps like Yuka and Foodvisor. We chose it because it aligns perfectly with Sophie's need for trusted, transparent nutritional data."

---

## SLIDE 6: OFF Data - Formats & What We Extract

**Say (40 seconds):**
"We access Open Food Facts through two methods."

"First: the REST API. We query 5 food categories daily, with rate limiting at 0.6 seconds between calls. This gives us about 1,000 new or updated products per day in JSON format."

"Second: the Parquet bulk export from HuggingFace. The full dump of 3 million+ products, filtered for France, giving us about 798,000 French products (all with completeness >= 0.3). This runs weekly."

"On the right, you can see a real example - Nutella, barcode 3017620422003. 31 fields: energy, fat, sugars, Nutri-Score D, NOVA group 4. But notice: the data is messy - inconsistent naming, missing values. That is why cleaning is critical."

---

## SLIDE 7: Data Cleaning - Before & After (C10)

**Say (50 seconds):**
"This is competency C10 - data aggregation and cleaning. Let me walk you through our 7 cleaning rules."

*(Point to each row)*
1. "Column rename: the API uses `energy-kcal_100g`, we standardize to `energy_kcal`"
2. "Barcode cleaning: strip non-numeric characters, remove trailing suffixes"
3. "Nutri-Score normalization: lowercase 'd' becomes uppercase 'D'"
4. "Range capping: if energy_kcal is 2000 per 100g, that is physiologically impossible - we set it to NULL"
5. "Null product names are deleted entirely - no name, no product"
6. "Deduplication: if the same barcode appears twice, we keep the record with the highest completeness score"
7. "Unit conversion: if we only have kJ and no kcal, we divide by 4.184"

"Result: 798,177 raw records become 777,126 clean records. A 2.6% removal rate -- PySpark removes invalid barcodes, null product names, and deduplicates by barcode. The output is `products_cleaned.parquet`."

---

## SLIDE 8: End-to-End Data Flow

**Say (40 seconds):**
"Here is the complete data flow, end to end."

"At 2 AM: 5 extraction scripts pull data from our sources into raw files. At 4 AM: PySpark runs the cleaning pipeline -- aggregates, validates, and cleans everything. At 4:30 AM: cleaned data is imported into the PostgreSQL app database. At 5 AM: the warehouse ETL and the data lake ingestion run in parallel."

"From there, all audiences are served through Streamlit - users, nutritionists, analysts, and admins each see role-specific dashboards. The ops team monitors through Grafana."

"This is fully automated with Apache Airflow."

---

## SLIDE 9: One Command, 15 Services

**Say (30 seconds):**
"The entire platform starts with one command: `docker compose up -d`."

"14 services organized in 4 groups: Core infrastructure - PostgreSQL, Redis, MinIO. Orchestration - Airflow with webserver, scheduler, and worker. Application layer - FastAPI and Streamlit with 4 role-based dashboards. Monitoring - Prometheus, Grafana, StatsD exporter, and MailHog for alerts."

"Why Docker Compose? Reproducibility. Any machine with Docker can run the full platform. This is critical for the demo and for handing the project off to Sophie's IT team."

> DEMO OPPORTUNITY: If you have time, you can show `docker compose ps` in a terminal.

---

## SLIDE 10: Tech Stack - What & Why

**Say (45 seconds):**
"Each tool was chosen for a reason."

"Extraction and cleaning: OFF API, BeautifulSoup for scraping, DuckDB for big data SQL on Parquet files. PySpark 3.5 for the cleaning pipeline -- distributed-capable, processes 798K rows in under 3 minutes. Three source types as required by C8."

"Orchestration: Airflow 2.8 over Prefect, because Airflow is more mature with better UI and Celery support for scaling."

"Storage: PostgreSQL for ACID transactions and RGPD delete support. MinIO as a free, self-hosted S3-compatible data lake. Redis for caching and as the Celery broker."

"Serving: FastAPI for async REST API with JWT auth. Streamlit as the single frontend with 4 role-based dashboards - replacing the need for a separate BI tool like Superset."

"Monitoring: Prometheus and Grafana with 6 dashboards. MailHog for SMTP alert emails. This covers C16."

---

## SLIDE 11: Key Technical Decisions (C3)

**Say (40 seconds):**
"Competency C3 requires documenting architecture decisions. Here are four key ones."

"PostgreSQL over MongoDB: we need ACID transactions for financial-grade data integrity, and row-level delete for RGPD compliance. MongoDB does not support transactional RGPD delete easily."

"Airflow over Prefect: more mature ecosystem, proven at scale, better UI for monitoring."

"MinIO over AWS S3: self-hosted means no cloud costs and no vendor lock-in. S3-compatible API so we could migrate to AWS later if needed."

"Streamlit multi-role over Superset: one fewer service to maintain, JWT-based RBAC built into the app, and the analyst gets product analytics and data catalog in the same interface as users."

---

## SLIDE 12: PostgreSQL - Three Zones

**Say (30 seconds):**
"We run everything in one PostgreSQL instance but with three logical zones."

"The `app` schema is the live application - products, users, meals. FastAPI and Streamlit read and write here."

"The `dw` schema is the warehouse - star schema with 7 dimensions and 2 fact tables. The Streamlit analyst dashboard reads from here via FastAPI."

"And MinIO is the data lake - bronze, silver, gold buckets in a medallion architecture. Only Parquet files. The gold layer includes 4 anonymized aggregate datasets: nutrition_patterns, popular_products, brand_rankings, and category_stats. Used by data scientists."

"ETL flows from app to warehouse, and in parallel from app to the lake."

---

## SLIDE 13: Why Both a Warehouse AND a Lake?

**Say (40 seconds):**
"A common question: why not just one?"

"The warehouse holds product data AND user data. It has ACID transactions, row-level RGPD delete, consent filtering per query, and sub-100ms dashboard queries. It serves BI analysts."

"The lake holds product data ONLY. Never user data. Why? Parquet files are immutable - you cannot delete one user's rows from a Parquet file. So for RGPD compliance, personal data must stay in PostgreSQL where we can delete individual records."

"This is a deliberate architecture decision driven by RGPD, not just by technology preferences."

---

## SLIDE 16: Data Topography (C2)

**Say (30 seconds):**
"C2 requires mapping all data in four dimensions."

"Semantics: 9 business objects documented in a business glossary with metadata."
"Data Models: structured data in PostgreSQL, semi-structured JSON from APIs, unstructured Parquet files."
"Flows: 8 source-to-target flows documented in a flux matrix with ETL diagrams."
"Access: role-based access matrix with 3 levels and RGPD constraints."

---

## SLIDE 17: System Architecture (C3)

**Say (20 seconds):**
"Here is the full architecture - 14 services with their ports. Three data sources feed into Airflow, which loads PostgreSQL and MinIO. PostgreSQL serves FastAPI. FastAPI serves Streamlit, which is the single frontend for all 4 roles. Prometheus collects metrics from all services and feeds Grafana."

"Each arrow represents a real network connection between Docker containers."

---

## SLIDE 18: Flux Matrix (C2, C3)

**Say (20 seconds):**
"The flux matrix documents all 8 data flows. Source, format, target, script name, and frequency. From the OFF API daily, to the Parquet weekly, to scraping monthly. Each flow has a dedicated Python script, all versioned on Git."

---

## SLIDE 19: Technical Monitoring (C4)

**Say (30 seconds):**
"C4 requires regular technical monitoring. I track three topics weekly, spending about 1 hour per week."

"Streamlit multi-role RBAC: we built a 4-role dashboard system with JWT-based access control, replacing the need for Superset. Applied in the project."
"GDPR Update: the EDPB issued guidelines in January 2026 saying wellness data is sensitive. We are compliant."
"Airflow 2.8: object storage backend and listener hooks. Noted for future implementation."

"All documented in `docs/veille_technologique.md` with verified source reliability."

---

## SLIDE 20: RGPD Compliance (C3, C11)

**Say (40 seconds):**
"RGPD is not an afterthought - it is built into the architecture."

"Four pillars:"
"Data Registry: a `rgpd_data_registry` table documenting the legal basis for each field and retention periods."
"Consent: mandatory checkbox at registration. Consent date is tracked. No consent, no account."
"Auto-Cleanup: a scheduled function `rgpd_cleanup_expired_data` that deletes meals older than 2 years and users past their retention date."
"Security: passwords hashed with bcrypt, users identified by UUID not email, and SHA256 pseudonymization in the warehouse."

"Critical point: personal data stays in PostgreSQL where we can do row-level delete. Public product data goes to both the warehouse and the lake."

---

## SLIDE 21: 6-Phase Roadmap (C5)

**Say (30 seconds):**
"The project was planned in 6 phases over 12 weeks. Setup in weeks 1-2, extraction in 3-4, transformation in 5-6, warehouse in 7-8, lake in 9-10, and deployment with monitoring in weeks 11-12."

"We used Fibonacci story points for estimation, Agile rituals - planning, standup, review, retrospective - and 5 defined roles: data engineer, platform engineer, CI/CD engineer, auditor, and reviewer."

---

## SLIDE 22: Tracking Indicators (C6)

**Say (20 seconds):**
"C6 requires tracking indicators. We track four: DAG success rate from Airflow, activity log entries - 22 entries over 14 days, completeness percentage per dataset, and ETL duration trends over time. Visible in Airflow UI and the Grafana SLA dashboard."

---

## SLIDE 23: Multi-Audience Communication (C7)

**Say (20 seconds):**
"C7 requires adapting communication to the audience. Developers get Swagger API docs, ReDoc, Grafana dashboards, and Git-based MkDocs. Analysts get the Streamlit Product Analytics dashboard and Data Catalog. Nutritionists get user analytics. End users get meal tracking and product search."

"Right tool for the right audience."

---

## SLIDE 24: 5 Extraction Sources (C8)

**Say (30 seconds):**
"C8 requires extraction from 5 source types. We have:"
"REST API: Open Food Facts, 1,000+ products per day."
"Data File: Parquet bulk export, 798K products."
"Web Scraping: ANSES and EFSA nutritional guidelines with BeautifulSoup."
"Database: direct PostgreSQL extraction."
"Big Data System: DuckDB running SQL directly on Parquet files - over 3 million rows without needing a database server. PySpark then handles the actual cleaning after DuckDB extracts."

"All 5 feed into `aggregate_clean.py` which merges and standardizes everything using PySpark."

---

## SLIDE 25: REST API Detail (C8)

**Say (20 seconds):**
"Here is the structure of `extract_off_api.py`. It configures 5 food categories, sends paginated GET requests, respects rate limiting at 0.6 seconds, includes a proper User-Agent header, wraps each page in try/except for error handling, and saves JSON to `/data/raw/api/`. All 5 extraction scripts follow this same structure."

---

## SLIDE 26: Scraping & DuckDB (C8)

**Say (20 seconds):**
"Two more source types. Web scraping targets ANSES and EFSA for official nutritional guidelines using BeautifulSoup, with fallback RDA values. Runs monthly."

"DuckDB handles extraction -- SQL directly on Parquet files, 3 million rows, no database needed, columnar storage means fast analytical scans. PySpark handles cleaning -- distributed transformation on 798K rows. DuckDB gets the data out, PySpark makes it clean."

---

## SLIDE 27: Cleaning Pipeline (C10)

**Say (20 seconds):**
"The 7 cleaning steps, all running in PySpark, in pipeline order: standardize column names, validate barcodes, remove null product names, cap nutritional values at physiological maximums, normalize Nutri-Score to uppercase, deduplicate by barcode keeping the most complete record, and generate a cleaning report. After cleaning, 6 formal data quality checks run: row count threshold, barcode uniqueness, null rates per column, range validation on nutritional fields, Nutri-Score value validation, and all results are logged to the `staging.data_quality_checks` table."

---

## SLIDE 28: 7 SQL Queries (C9)

**Say (20 seconds):**
"C9 requires optimized SQL extraction queries. We have 7, each using a different technique: full-text search with GIN index, window functions with ROW_NUMBER, CTEs to avoid repeated scans, analytical functions, LAG for temporal trends, GROUP BY with HAVING, and materialized views with complex joins. All documented with EXPLAIN ANALYZE output."

---

## SLIDE 29: RGPD-Compliant Database (C11)

**Say (30 seconds):**
"C11: creating the RGPD-compliant database. We followed the MERISE methodology: MCD to MLD to MPD."

"8 tables with full referential integrity. The `rgpd_data_registry` table in red documents every personal data field. Consent columns on the users table. A cleanup function for expired data. bcrypt password hashing and UUID-based identification."

---

## SLIDE 30: FastAPI REST API (C12)

**Say (45 seconds):**
"C12: the REST API. Eight endpoints covering authentication, product search, barcode lookup, healthier alternatives, meal logging, and nutrition summaries."

"The authentication flow:" *(point to the right side)*
"Step 1: user logs in with username and password."
"Step 2: the API creates a JWT token - a digitally signed string containing the user ID, role, and a 60-minute expiry."
"Step 3: on every subsequent request, the API decodes the token, checks the role, and enforces access control."
"Step 4: responses are validated with Pydantic schemas."

"Three roles: user sees their own data, nutritionist sees all user analytics, admin sees everything including the data catalog."

> DEMO: "Let me show you the Swagger UI at localhost:8000/docs"

---

## SLIDE 31: Streamlit - Two Roles (C7, C20)

**Say (30 seconds):**
"The Streamlit frontend has two parts. The user app on port 8501: product search, meal logging, daily macro dashboard, weekly trends, product comparison, and healthier alternatives. It consumes the FastAPI REST API."

"The data catalog page: search datasets, browse bronze/silver/gold layers, view schemas and lineage, check quality metrics, and see governance and RGPD information. It connects directly to MinIO."

> DEMO: "Let me show you the Streamlit app. I will log in as a regular user first, then as a nutritionist, then as admin to show the role-based access."

---

## SLIDE 32: Star Schema (C13)

**Say (30 seconds):**
"C13: warehouse modeling. We use a star schema with 7 dimension tables and 2 fact tables, following the Kimball bottom-up approach."

"Two fact tables: `fact_daily_nutrition` tracks user meal data, and `fact_product_market` tracks product availability and quality. They share `dim_product` and `dim_time`."

"Plus 6 datamart views that pre-compute common analytical queries so analysts do not need to write complex joins."

---

## SLIDE 33: 6 Datamart Views (C13, C14)

**Say (20 seconds):**
"Six pre-built views: daily nutrition tracking for nutritionists, product availability by category for market analysts, brand quality ranking, Nutri-Score distribution for public health, nutrition trends for data scientists, and DW health metrics for admins."

"Datamarts save analysts from writing star-schema joins - they just query a view."

---

## SLIDE 34: ETL Pipeline - 7 DAGs (C15)

**Say (30 seconds):**
"C15: the ETL pipeline, orchestrated by 7 Airflow DAGs."

"Three extraction DAGs run at 2 AM. The cleaning DAG runs at 4 AM. Then at 5 AM, the warehouse load and datalake ingest run in parallel."

"A seventh DAG handles backups and maintenance at 6 AM."

"Cross-DAG coordination uses `ExternalTaskSensor` - the warehouse and lake DAGs wait until cleaning finishes before starting."

> DEMO: "Let me show you the Airflow UI at localhost:8080"

---

## SLIDE 35: SCD - Slowly Changing Dimensions (C17)

**Say (30 seconds):**
"C17: dimension variations using the three Kimball types."

"Type 1 - Overwrite: used for `dim_brand`. If a brand name was misspelled, just correct it. No history needed for typos."

"Type 2 - Historical: used for `dim_product`. When a product's recipe changes, we close the old row with an end date and insert a new one. Full history preserved."

"Type 3 - Previous Value: used for `dim_country`. Keep one column for the previous value - one level of history."

"Change detection in the ETL uses `IS DISTINCT FROM` to detect which type of update to apply."

---

## SLIDE 36: Alert System (C16)

**Say (20 seconds):**
"When a DAG fails: the Airflow callback in `alerting.py` fires. It does three things simultaneously: logs to the `activity_log` table, sends an email via MailHog, and pushes a metric to StatsD. StatsD feeds Prometheus, which feeds Grafana. The ops team sees alerts on the Grafana dashboard and in their inbox."

---

## SLIDE 37: SLA Dashboard (C16)

**Say (20 seconds):**
"Four SLA indicators: ETL success rate above 95%, data freshness under 24 hours, backup completion at 100%, and query response time under 5 seconds."

"Incidents are prioritized using an ITIL matrix: P1 critical under 1 hour, P2 high under 4 hours, P3 medium under 24 hours, P4 low goes to the next sprint. Escalation goes from auto-restart to engineer to architecture review."

> DEMO: "Let me show Grafana at localhost:3000 and MailHog at localhost:8025"

---

## SLIDE 38: Backup & Maintenance (C16)

**Say (20 seconds):**
"The backup script `backup_database.py` supports full and partial modes. Backups are uploaded to the MinIO /backups bucket with automatic cleanup of old backups. It runs as a scheduled Airflow DAG."

"We also documented procedures for: adding a new data source in 6 steps, creating new access in 3 steps, expanding storage, adding datamart views, and scaling compute capacity. All in chapter 12 of the final report."

---

## SLIDE 39: Medallion Architecture (C18)

**Say (30 seconds):**
"C18: the data lake architecture. We use the medallion pattern with three layers."

"Bronze: raw data as-is. JSON, Parquet, CSV. 90-day retention."
"Silver: cleaned and validated. Parquet only. Deduplicated."
"Gold: analytics-ready aggregates. 4 anonymized datasets: nutrition_patterns (macro averages by Nutri-Score), popular_products (top items by completeness), brand_rankings (brand quality scores), and category_stats (per-category nutritional summaries). Daily snapshots."

"Data flows from bronze to silver through cleaning, and from silver to gold through aggregation."

"This addresses the three V's: Volume - 3 million+ products in the source, 798K imported and cleaned with PySpark. Variety - JSON, Parquet, CSV. Velocity - daily and weekly schedules."

---

## SLIDE 40: Volume, Variety, Velocity (C18)

**Say (15 seconds):**
"Just to be explicit about the three V's: Volume is 3 million+ products with Parquet columnar format for fast scans. Variety is 4 formats - JSON, Parquet, HTML, SQL. Velocity is daily API pulls, weekly Parquet, monthly scraping, all scheduled as DAGs."

---

## SLIDE 41: Catalog Comparison (C18)

**Say (30 seconds):**
"We compared three catalog tools. Apache Atlas: powerful but heavy, requires Java, overkill for our scale. DataHub: moderate overhead, requires its own infrastructure. Our custom JSON catalog: minimal overhead, native MinIO integration, right-sized for this project."

"We chose the custom approach because it gives us search and browse capabilities through the Streamlit page without adding significant infrastructure. If the project grows, migrating to DataHub would be the natural next step."

---

## SLIDE 42: Data Catalog Browser (C20)

**Say (20 seconds):**
"The catalog browser is a Streamlit page. You can search datasets by name, format, or source. Browse by layer - bronze, silver, gold tabs. View schema with column names and types. See data lineage - where each dataset came from. Check quality metrics. And review governance and RGPD compliance information, including access groups and retention policies."

> DEMO: "Let me show the catalog. I need to log in as admin because the catalog is restricted by role."

---

## SLIDE 43: Access Governance (C21)

**Say (30 seconds):**
"C21: data governance with group-based access control."

"Three groups, applied consistently across all four systems:"
"Admin role: full access to PostgreSQL, all MinIO buckets, all API endpoints, and all Streamlit pages."
"Analyst role: read products in PostgreSQL, gold bucket in MinIO, analytics API, and Streamlit Product Analytics plus Data Catalog."
"Nutritionist role: read products and meals in PostgreSQL, nutritionist API, and Streamlit User Dashboard."
"User role: own meals only in PostgreSQL, basic API endpoints, and 6 Streamlit pages."

"The principle is least privilege: each role gets only what it needs. And access is by group, not individual, as RGPD recommends."

---

## SLIDE 44: Monitoring Stack (C16, C20)

**Say (15 seconds):**
"Four exporters feed Prometheus: StatsD for Airflow metrics, cAdvisor for Docker container stats, Node Exporter for host metrics, and PostgreSQL Exporter for database metrics. Prometheus scrapes all four and feeds Grafana's 6 dashboards."

---

## SLIDE 45: 6 Grafana Dashboards

**Say (15 seconds):**
"Six dashboards: Airflow overview for DAG runs, Airflow DAGs for per-DAG performance, PostgreSQL for database health, Docker System for container resources, MinIO for object storage, and SLA Compliance for the four service indicators."

---

## SLIDE 46: 21/21 Competencies Covered

**Say (20 seconds):**
"All 21 competencies across all 4 blocks are covered by this single integrated project. Block 1 - steer a data project: C1 through C7. Block 2 - data collection: C8 through C12. Block 3 - warehouse: C13 through C17. Block 4 - lake: C18 through C21."

"One project, 15 Docker services, full RGPD compliance, all 7 evaluations."

---

## SLIDE 47: Lessons Learned

**Say (30 seconds):**
"What worked well: Docker for one-command deployment. Running the warehouse and lake in parallel. Airflow for orchestration. Making RGPD an architecture driver from day one, not a bolt-on. And treating documentation as a first-class deliverable."

"Next steps: real-time streaming with Kafka, Kubernetes for production orchestration, an ML pipeline for personalized recommendations, migrating to DataHub for the catalog, and more automated testing."

---

## SLIDE 48: Live Demo Plan

**Say (15 seconds):**
"Here is the demo sequence. I will go through these in order during the presentation."

> This is your checklist. Refer to it as you move through the demos.

---

## SLIDE 49: Thank You

**Say:**
"Thank you for your attention. The code is on GitHub at Reetika12795/NutriTrack. I am ready for your questions."

---

# General Tips

1. **Always tie features back to Sophie.** "We built this because Sophie needs to..."
2. **Mention the competency number** when you show something relevant: "This is C8" or "This covers C16."
3. **During demos, narrate what you are doing.** "I am now logging in as a nutritionist to show the role-based access control."
4. **If something fails in the demo**, stay calm and say: "Let me show you an alternative." Move to the next demo point.
5. **Keep track of time.** You have 60 minutes for E1-E5 - that is about 90 seconds per slide.
6. **For the Q&A (E6, 10 min):** The jury will ask about warehouse maintenance. Be ready to explain: alert flow, SLA metrics, backup procedures, and how you add a new data source.
7. **For E7 (10 min):** Focus on the medallion architecture, the catalog tool comparison, and access governance.
8. **Speak slowly and clearly.** It is better to cover fewer slides well than to rush through all of them.
