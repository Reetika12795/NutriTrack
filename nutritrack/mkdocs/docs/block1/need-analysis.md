# Client and Need Analysis

**Competencies**: C1 (Need Analysis), C2 (Data Topography), C4 (Technical Monitoring)
**Evaluation**: E1 (interview grids), E2 (professional report)

---

## Project Context

Sophie Yang, a freelance nutritionist with 120+ clients, tracks patient nutrition using spreadsheets and paper food diaries. She needs a digital platform to:

- Let patients log meals and track daily nutrition
- Provide reliable nutritional data for French food products
- Generate analytical reports on patient cohorts
- Comply with RGPD for health-related personal data

!!! tip "SMART Objectives"
    1. **S**: Build a meal-tracking platform using Open Food Facts data for French products
    2. **M**: Integrate 500K+ products with Nutri-Score and NOVA classification
    3. **A**: Deploy on Docker Compose with zero CAPEX, under 100 EUR/year OPEX
    4. **R**: Cover all 21 competencies of the RNCP37638 certification
    5. **T**: Deliver a working prototype within 3 months

## Interview Grid: Data Producers

Questions for stakeholders who generate or maintain data:

| # | Question | Purpose |
|---|----------|---------|
| 1 | What data do you currently collect about food products? | Identify existing data assets |
| 2 | In what format is the data stored (spreadsheet, database, files)? | Assess data maturity |
| 3 | How frequently is the data updated? | Determine velocity requirements |
| 4 | Who is responsible for data quality and corrections? | Identify data stewards |
| 5 | Are there any regulatory constraints on the data you manage? | RGPD and health data compliance |
| 6 | What metadata do you associate with each record? | Schema and catalog planning |
| 7 | How do you handle data corrections or retractions? | SCD and versioning strategy |
| 8 | What volume of new records do you expect per month? | Capacity planning |

## Interview Grid: Data Consumers

Questions for stakeholders who use data for decisions:

| # | Question | Purpose |
|---|----------|---------|
| 1 | What analyses do you currently perform on nutritional data? | Define analytical requirements |
| 2 | What time granularity do you need (daily, weekly, monthly)? | Design time dimensions |
| 3 | Do you need to compare across brands, categories, or countries? | Identify dimension axes |
| 4 | What format do you prefer for reports (tables, charts, exports)? | Choose visualization tools |
| 5 | How quickly do you need results after data collection? | Set SLA targets |
| 6 | Do you need historical trend analysis or only current state? | SCD requirements |
| 7 | Who else in your organization needs access to these analyses? | RBAC and access planning |
| 8 | What accessibility requirements do you have for the tools? | Accessibility compliance |

## Data Topography (C2)

### Part 1: Semantics and Metadata

| Business Object | Description | Key Metadata |
|----------------|-------------|-------------|
| Product | A food product identified by barcode | barcode, product_name, nutriscore_grade, nova_group |
| Nutritional Values | Per-100g nutrient breakdown | energy_kcal, fat, sugars, salt, proteins, fiber |
| Brand | Product manufacturer | brand_name, parent_company |
| Category | Product classification | category_name, parent_category |
| User | Platform user (patient or nutritionist) | email, role, activity_level, consent status |
| Meal | A logged meal event | date, meal_type, items with quantities |

### Part 2: Data Models

| Source | Structure | Format |
|--------|-----------|--------|
| Open Food Facts API | Semi-structured | JSON (nested, variable fields) |
| OFF Parquet dump | Structured | Columnar Parquet (200+ columns) |
| ANSES/EFSA guidelines | Semi-structured | HTML tables scraped to JSON |
| User-generated data | Structured | PostgreSQL relational tables |

### Part 3: Treatments and Data Flows

See the [Data Flow](../overview/data-flow.md) page for the complete flux matrix and pipeline diagram.

### Part 4: Access and Usage Conditions

| Data | Access Level | Conditions |
|------|-------------|------------|
| Open Food Facts | Public | Open Database License (ODbL) |
| ANSES guidelines | Public | French government open data |
| User personal data | Restricted | RGPD consent required, encrypted at rest |
| Aggregated analytics | Role-based | Analyst and admin roles only |

## Synthesis Note

The feasibility study confirmed:

- **Need**: A clear gap exists between manual nutrition tracking and digital-native solutions
- **Data availability**: Open Food Facts provides 798K French products under open license
- **Technical feasibility**: Docker Compose can host all components on a single machine
- **RGPD**: Personal data limited to user profiles and meal logs; consent-based, with automated cleanup
- **Budget**: Zero CAPEX with open-source stack; OPEX under 100 EUR/year (domain + optional hosting)
