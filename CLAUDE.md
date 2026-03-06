# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

This is the **source of truth** for tracking progress on the final project for the certification **"Expert en infrastructures de donnees massives" (Data Engineer) - RNCP37638 - Level 7 (Master's equivalent)**.

Before starting any work session, review this file to understand which competencies are being addressed, validate current progress, and decide on next steps.

---

## Certification Overview

The certification consists of **4 competency blocks** with **21 competencies (C1-C21)** evaluated across **7 evaluations (E1-E7)**. All 4 blocks must be validated to obtain the title. There is no required order for passing the blocks.

### Final Oral Defense: 90 minutes total
- **60 min**: Presentation of evaluations E1-E5 (or a single project aggregating all), including a live demo and a simulated project kickoff meeting (E3)
- **10 min**: Q&A with jury on E6 report
- **10 min**: Presentation of E7
- **10 min**: Jury questions

---

## Block 1: Piloter la conduite d'un projet data (Steer a data project)

### E1 - Case Study (C1) | Recap PDF slide: E1
**Type**: Case study (real or fictitious)
**Competency**: C1
**Deliverable**: Interview grids
**Oral**: 5-minute presentation of grids

| Competency | Description | Key Evaluation Criteria |
|---|---|---|
| **C1** | Analyze a data project need expression in a feasibility study by exploring the business need with stakeholders to validate orientations and select technical hypotheses | Grids question business activities involved in the data project; grids question data characterization, metadata, access, storage, and applied treatments |

**What the candidate must produce:**
- Interview grid for business users who **produce** data
- Interview grid for business users who **consume** data (or will)

**Detailed criteria** (Referential p.3-4):
- Grids question business activities involved in the data project
- Grids question data characterization (metadata, access, storage, treatments)
- Synthesis note covers: need analysis, functional scope, available means, feasibility, data governance
- Synthesis note structure: intro (context, stakes, need reformulation), objectives & scope, opportunity study (interview synthesis, benchmark), feasibility study, conclusions (RICE analysis)
- SMART objectives
- Pre-project includes: macro technical recommendations, accessibility accommodations, RGPD compliance actions

---

### E2 - Professional Situation (C1, C2, C3, C4, C6) | Recap PDF slide: E2
**Type**: Professional simulation
**Competencies**: C1, C2, C3, C4, C6
**Deliverable**: Professional report (10-15 pages)
**Oral**: 20-minute project presentation

| Competency | Description | Key Evaluation Criteria |
|---|---|---|
| **C1** | Analyze a data project need expression | (see E1 above) |
| **C2** | Map available data by referencing usage, sources, metadata and data to validate technical hypotheses | Complete data topography with 4 parts: semantics/metadata, data models, treatments & data flows, data access & usage conditions |
| **C3** | Design a technical data exploitation framework by analyzing technical/means constraints and data mapping to define an adapted technical response (RGPD-compliant, eco-responsible) | Technical study covers: functional analysis, non-functional needs, functional/applicative/infrastructure/operational representations, architecture decisions, RGPD processes, eco-responsibility strategy, risks & costs |
| **C4** | Conduct technical and regulatory monitoring by selecting sources and processing collected information to formulate project recommendations | Monitoring theme covers a tool/regulation used in the project; regular schedule (min 1h/week); appropriate aggregation tools; accessibility-compliant communications; source reliability criteria verified |
| **C6** | Supervise data project execution by organizing methods, tools and communication between stakeholders | Adapted exchange facilitation; tracking tools configured & accessible; rituals documented; indicators updated throughout project |

**What the candidate must produce:**
1. Synthesis note on data need understanding
2. Formalized pre-project
3. Data topography (available and needed data)
4. Technical architecture study
5. Operational and financial report
6. Lessons learned / experience feedback on problems and trade-offs
7. Technical monitoring newsletter/bulletin

**Detailed criteria for C2** (Referential p.5-6):
- Data topography structured in 4 parts:
  - **Semantics**: metadata and business objects in a business glossary
  - **Data models**: how data is modeled/stored (structured, semi-structured, unstructured)
  - **Treatments & flows**: transformation, manipulation and processing methods across different IS
  - **Access & usage conditions**: data availability and access conditions

**Detailed criteria for C3** (Referential p.6-7):
- Technical study must include:
  - Functional analysis (what does the system do? business constraints?)
  - Non-functional needs (tools & technical constraints)
  - Functional, applicative, infrastructure, operational representations
  - Architecture decisions documentation
  - RGPD compliance processes (personal data registry, sorting/deletion treatments)
  - Eco-responsibility strategy (following government RGESN framework)
  - Risks and costs
  - Applicative representation contains a **flux matrix**
  - Technical choices must respect project objectives AND mobilizable means
  - Accessibility of deliverables anticipated with workstation adaptation solutions

---

### E3 - Role Play / Practical Case (C5, C6, C7) | Recap PDF slide: E3
**Type**: Role play - simulated project kickoff meeting
**Competencies**: C5, C6, C7
**Deliverable**: Presentation support + associated documents (pre-project, roadmap, calendar, communication strategy)
**Oral**: 10-minute simulation of kickoff meeting introduction

| Competency | Description | Key Evaluation Criteria |
|---|---|---|
| **C5** | Plan data project execution by attributing necessary means and defining milestones, methods and tracking to organize implementation | Team composition covers required skills; budget allocation; roadmap broken into major stages respecting functional scope; calendar with tasks/deliverables/dates/resource attribution/effort weighting/rituals; risk evaluation per stage |
| **C6** | Supervise data project execution | (see E2 above) |
| **C7** | Communicate throughout the data project on orientations, achievements and impacts by elaborating communication strategy and supports to inform all stakeholders | All communication steps planned (launch, milestones, demos, delivery); accessible supports; adapted content/discourse to audience; communications present chosen orientations and trade-offs |

**What the candidate must produce:**
1. Oral defense of the pre-project
2. Project roadmap presentation
3. Production calendar with scope assignments
4. Project tracking method + associated tools and rituals
5. Internal project communication strategy

**Detailed criteria for C5** (Referential p.9-10):
- Calendar accounts for: tasks & deliverables with deadlines, resource attribution, effort weighting, collaborative rituals
- Effort weighting uses a shared method (poker planning, equivalent unit method, etc.)
- Tracking tool configuration coherent with deadlines and mission attributions
- Planning elements communicated in accessible format
- Task sequencing enables each task's completion

**Detailed criteria for C7** (Referential p.11-12):
- User documentation production tasks are planned and distributed
- End-user onboarding sessions are planned
- Stakeholder feedback collection follows a process integrated into communication strategy

---

## Block 2: Realiser la collecte, le stockage et la mise a disposition des donnees (Data collection, storage & sharing)

### E4 - Professional Situation (C8, C9, C10, C11, C12) | Recap PDF slide: E4
**Type**: Professional simulation
**Competencies**: C8, C9, C10, C11, C12
**Deliverable**: Professional report (5-10 pages)
**Oral**: 15-minute project presentation

| Competency | Description | Key Evaluation Criteria |
|---|---|---|
| **C8** | Automate data extraction from web services, web pages (scraping), data files, databases and big data systems by programming adapted scripts | Extraction from a mix of: REST API, data file, scraping, database, big data system. Script has: entry point, dependency init, external connections, logic rules, error handling, result saving. Versioned on Git |
| **C9** | Develop SQL-type extraction queries from DBMS and big data systems | Queries are functional (targeted data effectively extracted); documentation highlights selection/filtering/join choices and query optimizations |
| **C10** | Develop data aggregation rules from different sources by programming corruption removal and format homogenization | Script is functional (data aggregated, cleaned, normalized into single dataset); versioned on Git; documentation covers dependencies, commands, algorithm logic, cleaning/homogenization choices |
| **C11** | Create a RGPD-compliant database by elaborating conceptual and physical data models and programming import | MERISE models; functional physical model; DB chosen based on modeling & project constraints; installation procedures reproducible; import script functional & documented on Git; personal data treatment registry; RGPD sorting procedures |
| **C12** | Share the dataset by configuring software interfaces and creating programmable interfaces (API) | REST API documentation covers all endpoints, auth/authz rules, follows standards (e.g. OpenAPI); API is functional for data access (restricted) and data retrieval |

**What the candidate must produce:**
1. Project presentation with context
2. Technical specifications (data source connections, collection, aggregation, storage; REST API and DB access)
3. Git repository access for all scripts
4. Live demo of script execution
5. Logical and technical explanation of all scripts
6. SQL query logic for data collection
7. Data models (conceptual, logical, physical - MCD, MLD, MPD)
8. Technical documentation for: collection scripts, import script, DB installation, import-to-DB script, REST API, DB access
9. REST API demo with HTTP client showing different access rules
10. RGPD compliance analysis
11. Conclusions on learnings and planned improvements

---

## Block 3: Elaborer et maintenir un entrepot de donnees (Data Warehouse)

### E5 - Professional Situation (C13, C14, C15) | Recap PDF slide: E5
**Type**: Professional simulation
**Competencies**: C13, C14, C15
**Deliverable**: Professional report (5-10 pages)
**Oral**: 10-minute project presentation

| Competency | Description | Key Evaluation Criteria |
|---|---|---|
| **C13** | Model data warehouse structure using dimensions and facts to optimize data organization for analytical queries | Data needed for analyses listed exhaustively; logical and physical models without interpretation errors; modeling applies DW practices (snowflake, star, constellation); top-down vs bottom-up approach justified |
| **C14** | Create a data warehouse from project parameters, technical/material constraints and data structure modeling | DW is functional; main configurations explained; source data access correctly configured; analyst access to DW/datamarts configured; test procedure covers full technical/functional spectrum; technical doc details architecture + install/config procedure; tech stack experience feedback |
| **C15** | Integrate necessary ETLs for data warehouse input/output to ensure data quality and correct formatting | Data formats and volumes known/explained; ETLs fed with identified data; output formats known/explained; outputs respect expected format; ETLs apply schema-compliant treatments; ETLs apply cleaning treatments (format/unit uniformity, duplicate detection); ETL logic clearly explained |

**What the candidate must produce:**
1. List of data needed for planned analyses
2. Logical and physical models of DW and datamarts
3. Tool configuration for DW and datamarts
4. Data access configuration for analysis teams
5. Source data access configuration
6. Test phase organization
7. Technical documentation
8. Tech stack experience feedback (coherence with project, advantages, difficulties)
9. ETL source integration and output zone configuration
10. Data treatment programming (cleaning, formatting per physical schema)

---

### E6 - Case Study (C16, C17) | Recap PDF slide: E6
**Type**: Case study
**Competencies**: C16, C17
**Deliverable**: Professional report (5-10 pages)
**Oral**: 5-10 minute Q&A based on report

| Competency | Description | Key Evaluation Criteria |
|---|---|---|
| **C16** | Manage the data warehouse using admin and supervision tools (RGPD-compliant) to ensure correct access, structural evolution integration, and operational maintenance | Activity logging with alert/error categories; alert system (email/sms/notification) on errors; maintenance tasks prioritized and assigned; SLA-based service indicators on dashboard; scheduled full/partial backups functional; documentation covers: new source integration, new access creation, storage space, datamarts, compute capacity; new sources correctly configured; ETLs updated; new accesses configured; RGPD personal data registry and sorting procedures |
| **C17** | Implement dimension variations in the data warehouse using the adapted method (Kimball type 1, 2, 3) to historize organizational activity evolution | Variation modeling fully integrates source data changes; modeling enables change historization; variations integrated into DW respecting initial modeling; ETLs updated; documentation updated with variations |

**What the candidate must produce:**
1. Maintenance methodology and tooling (task distribution, prioritization, indicator tracking - e.g. ITIL service desk, ticketing)
2. Alert and error logging configuration
3. Full and partial backup procedures
4. New data source integration
5. New access additions to DW
6. Evolution and scalability procedures documentation (access creation, datamart addition, storage increase)
7. Dimension variation modeling (Kimball type 1, 2, or 3)
8. Variation integration into DW
9. Variation integration into affected ETLs
10. Variation documentation + logical and physical model updates

---

## Block 4: Encadrer la collecte massive et la mise a disposition des donnees avec un data lake (Data Lake)

### E7 - Professional Situation (C18, C19, C20, C21) | Recap PDF slide: E7
**Type**: Professional simulation
**Competencies**: C18, C19, C20, C21
**Deliverable**: Professional report (individual)
**Oral**: 10-minute presentation (within the 90-min defense)

| Competency | Description | Key Evaluation Criteria |
|---|---|---|
| **C18** | Design data lake architecture by selecting appropriate technologies based on volume, variety and velocity to define optimal technical architecture | Technical proposals coherent with exploitation framework; architecture schema accounts for volume/velocity/variety constraints; schema uses appropriate formalism; multiple catalogs compared; selected catalog meets exploitability and access rights constraints |
| **C19** | Integrate data lake infrastructure components using adapted procedures to ensure acquisition, storage and catalog availability | Installation procedure documentation complete; installation runs without errors in test environment; storage system installed and functional; batch and real-time tools functional and connected to storage; catalog connected to storage; documentation covers install/config of storage, batch tools, and catalog tool |
| **C20** | Manage the data catalog considering data nature, feed sources and lifecycle (RGPD-compliant) | Feed method choices justified and appropriate per source; feed scripts run without errors; data correctly imported; metadata integrated into catalog; deletion procedures comply with access/regulatory/operational constraints; monitoring tracks material and application conditions; monitoring generates alerts on service disruption; RGPD registry and sorting procedures |
| **C21** | Implement data governance rules by securing search, retrieval and addition of data to respect organizational governance rules | Rights applied to groups (not individuals) when possible; access meets group needs; access limited to necessary resources; access RGPD-compliant; documentation covers access groups, associated rights, and update procedures |

**What the candidate must produce:**
1. Technical choices based on IT constraints, target issues, and data nature
2. Architecture schema addressing Volume, Velocity, and/or Variety needs
3. Catalog tool comparison and justified selection
4. Storage system installation procedure documentation
5. Installation procedure tested in dev environment (VM or containers)
6. Batch and real-time tool programs
7. Functional catalog demo connected to storage system
8. Per-source feed method selection and scripts
9. Catalog metadata updates
10. Update and deletion procedures based on lifecycle
11. Storage system monitoring demo (available space, memory, server status)
12. Feed rights configuration
13. Index search access rights configuration
14. Data retrieval access rights configuration
15. Groups and rights documentation (group and individual rights)

---

## Competency-to-Evaluation Cross-Reference

| Competency | Block | Evaluation(s) | Referential Pages |
|---|---|---|---|
| C1 | 1 | E1, E2 | p.3-4 |
| C2 | 1 | E2 | p.5-6 |
| C3 | 1 | E2 | p.6-7 |
| C4 | 1 | E2 | p.7-8 |
| C5 | 1 | E3 | p.9-10 |
| C6 | 1 | E2, E3 | p.10-11 |
| C7 | 1 | E3 | p.11-12 |
| C8 | 2 | E4 | p.12-14 |
| C9 | 2 | E4 | p.14 |
| C10 | 2 | E4 | p.14-15 |
| C11 | 2 | E4 | p.15-17 |
| C12 | 2 | E4 | p.17 |
| C13 | 3 | E5 | p.17-18 |
| C14 | 3 | E5 | p.18-19 |
| C15 | 3 | E5 | p.19-20 |
| C16 | 3 | E6 | p.20-22 |
| C17 | 3 | E6 | p.22 |
| C18 | 4 | E7 | p.22-23 |
| C19 | 4 | E7 | p.23-24 |
| C20 | 4 | E7 | p.24-25 |
| C21 | 4 | E7 | p.25 |

---

## Deliverables Summary

| Evaluation | Type | Deliverable | Oral Duration |
|---|---|---|---|
| E1 | Case Study | Interview grids | 5 min |
| E2 | Professional Situation | Professional report (10-15 pages) | 20 min |
| E3 | Role Play | Presentation + docs (pre-project, roadmap, calendar, comms strategy) | 10 min |
| E4 | Professional Situation | Professional report (5-10 pages) | 15 min |
| E5 | Professional Situation | Professional report (5-10 pages) | 10 min |
| E6 | Case Study | Professional report (5-10 pages) | 5-10 min Q&A |
| E7 | Professional Situation | Professional report (individual) | 10 min |

---

## Project Progress Tracker

Use the checklist below to track which competencies and evaluations have been addressed during the project. Update as work progresses.

### Block 1: Steer a data project
- [ ] **E1** (C1) - Interview grids
- [ ] **E2** (C1, C2, C3, C4, C6) - Professional report
- [ ] **E3** (C5, C6, C7) - Kickoff meeting simulation

### Block 2: Data collection, storage & sharing
- [ ] **E4** (C8, C9, C10, C11, C12) - Professional report

### Block 3: Data Warehouse
- [ ] **E5** (C13, C14, C15) - Professional report
- [ ] **E6** (C16, C17) - Professional report

### Block 4: Data Lake
- [ ] **E7** (C18, C19, C20, C21) - Professional report

---

## Source Documents
- `Recap_Certif_Data Engineer.pdf` - Certification summary with evaluation descriptions and deliverables
- `[DE] Referentiel Activites Competences et evaluation.pdf` - Full official referential (28 pages) with detailed activities, competencies, evaluation criteria, and glossary (p.26-28)
